from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import TokenService
from src.enums import AccountStatus, BasicRole
from src.exceptions import AccessDenied, AppException, Conflict, NotFound, ValidationError, VersionConflict
from src.logger import logger
from src.rabbit import Response, err
from src.relation.enums import RelationStatus, RelationType
from src.relation.models import UserRelation
from src.relation.repository import UserRelationRepository
from src.relation.schemas import (
    AttachParentRequest,
    AttachStudentRequest,
    CreateStudentRequest,
    ListStudentsRequest,
    ListTutorsRequest,
    RelationIdRequest,
    RelationRead,
    StudentListItem,
    TutorListItem,
    UpdateParentRightsRequest,
    UpdateRelationRequest,
)
from src.schemas import Page
from src.user.models import User
from src.user.repository import UserRepository
from src.user.schemas import UserRead


class RelationService:
    """Бизнес-логика связей человек-человек (ученики, репетиторы, родители)"""

    def __init__(
        self,
        *,
        session: AsyncSession,
        users: UserRepository,
        relations: UserRelationRepository,
        tokens: TokenService,
    ) -> None:
        self.session = session
        self.users = users
        self.relations = relations
        self.tokens = tokens

    async def _current_user(self, token: str) -> User:
        """Достаёт вызывающего из JWT и его профиль"""
        claims = self.tokens.decode(token)
        user = await self.users.get_by_user_id(claims.user_id)
        if user is None:
            logger.debug(f"[RelationService] No profile for caller {claims.user_id}")
            raise NotFound("Profile not found")
        return user

    async def _owned_relation(self, caller: User, relation_id: int) -> UserRelation:
        """Возвращает связь, если вызывающий — её инициатор (from_user)"""
        relation = await self.relations.get_by_id(relation_id)
        if relation is None or relation.deleted_at is not None:
            raise NotFound("Relation not found")
        if relation.from_user_id != caller.id:
            logger.debug(f"[RelationService] Caller {caller.id} is not owner of relation {relation_id}")
            raise AccessDenied()
        return relation

    async def create_student(self, request: CreateStudentRequest) -> Response[RelationRead]:
        try:
            tutor = await self._current_user(request.access_token)
            card = await self.users.create(
                basic_role=BasicRole.student,
                account_status=AccountStatus.managed,
                first_name=request.first_name,
                last_name=request.last_name,
                middle_name=request.middle_name,
                nickname=request.nickname,
                date_of_birth=request.date_of_birth,
                contacts=request.contacts,
                messengers=request.messengers,
                timezone=request.timezone,
                locale=request.locale,
            )
            relation = await self.relations.create(
                from_user_id=tutor.id,
                to_user_id=card.id,
                relation_type=RelationType.tutor_of,
                subjects=request.subjects,
                level=request.level,
                notes=request.notes,
                tags=request.tags,
            )
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(data=RelationRead.model_validate(relation))

    async def attach_student(self, request: AttachStudentRequest) -> Response[RelationRead]:
        try:
            tutor = await self._current_user(request.access_token)
            relation = await self._create_link(
                from_user_id=tutor.id,
                to_user_id=request.student_id,
                relation_type=RelationType.tutor_of,
                subjects=request.subjects,
                level=request.level,
                notes=request.notes,
                tags=request.tags,
            )
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(data=RelationRead.model_validate(relation))

    async def attach_parent(self, request: AttachParentRequest) -> Response[RelationRead]:
        try:
            caller = await self._current_user(request.access_token)
            student = await self.users.get_by_id(request.student_id)
            if student is None:
                raise NotFound("Student not found")
            if await self.users.get_by_id(request.parent_id) is None:
                raise NotFound("Parent not found")
            # Родителя прикрепляет тот, кто связан с учеником (репетитор), либо сам родитель
            if caller.id != request.parent_id and not await self.relations.exists_link(caller.id, request.student_id):
                logger.debug(f"[RelationService] Caller {caller.id} cannot attach parent to {request.student_id}")
                raise AccessDenied()
            relation = await self._create_link(
                from_user_id=request.parent_id,
                to_user_id=request.student_id,
                relation_type=RelationType.parent_of,
                parent_rights=request.parent_rights,
            )
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(data=RelationRead.model_validate(relation))

    async def list_students(self, request: ListStudentsRequest) -> Response[Page[StudentListItem]]:
        try:
            tutor = await self._current_user(request.access_token)
        except AppException as exc:
            return err(exc.status, exc.message)

        rows, total = await self.relations.list_students(
            from_user_id=tutor.id,
            offset=request.offset,
            limit=request.limit,
            status=request.status,
            subject=request.subject,
            tag=request.tag,
            group_row=request.group_row,
            search=request.search,
            sort=request.sort,
            descending=request.descending,
        )
        items = [
            StudentListItem(relation=RelationRead.model_validate(rel), student=UserRead.model_validate(user))
            for rel, user in rows
        ]
        page = Page(items=items, total=total, offset=request.offset, limit=request.limit)
        return Response(data=page)

    async def list_tutors(self, request: ListTutorsRequest) -> Response[Page[TutorListItem]]:
        try:
            caller = await self._current_user(request.access_token)
        except AppException as exc:
            return err(exc.status, exc.message)

        rows, total = await self.relations.list_tutors(to_user_id=caller.id, offset=request.offset, limit=request.limit)
        items = [
            TutorListItem(relation=RelationRead.model_validate(rel), tutor=UserRead.model_validate(user))
            for rel, user in rows
        ]
        page = Page(items=items, total=total, offset=request.offset, limit=request.limit)
        return Response(data=page)

    async def update_relation(self, request: UpdateRelationRequest) -> Response[RelationRead]:
        try:
            caller = await self._current_user(request.access_token)
            await self._owned_relation(caller, request.relation_id)
            values = self._build_relation_values(request)
            if not values:
                relation = await self.relations.get_by_id(request.relation_id)
                return Response(data=RelationRead.model_validate(relation))
            updated = await self.relations.update(id=request.relation_id, version=request.version, values=values)
            if updated is None:
                raise VersionConflict()
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(data=RelationRead.model_validate(updated))

    async def update_parent_rights(self, request: UpdateParentRightsRequest) -> Response[RelationRead]:
        try:
            caller = await self._current_user(request.access_token)
            relation = await self._owned_relation(caller, request.relation_id)
            if relation.relation_type != RelationType.parent_of:
                raise ValidationError("Relation is not parent_of")
            updated = await self.relations.update(
                id=request.relation_id,
                version=request.version,
                values={UserRelation.parent_rights: request.parent_rights},
            )
            if updated is None:
                raise VersionConflict()
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(data=RelationRead.model_validate(updated))

    async def archive_relation(self, request: RelationIdRequest) -> Response[RelationRead]:
        try:
            caller = await self._current_user(request.access_token)
            await self._owned_relation(caller, request.relation_id)
            updated = await self.relations.update(
                id=request.relation_id,
                version=request.version,
                values={UserRelation.status: RelationStatus.archived},
            )
            if updated is None:
                raise VersionConflict()
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(data=RelationRead.model_validate(updated))

    async def delete_relation(self, request: RelationIdRequest) -> Response[RelationRead]:
        try:
            caller = await self._current_user(request.access_token)
            await self._owned_relation(caller, request.relation_id)
            updated = await self.relations.soft_delete(id=request.relation_id, version=request.version)
            if updated is None:
                raise VersionConflict()
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(message="Relation deleted", data=RelationRead.model_validate(updated))

    async def _create_link(
        self,
        *,
        from_user_id: int,
        to_user_id: int,
        relation_type: RelationType,
        subjects: list | None = None,
        level: str | None = None,
        notes: str | None = None,
        tags: list | None = None,
        parent_rights: dict | None = None,
    ) -> UserRelation:
        """Создаёт связь с проверками на самосвязь и дубли активных связей"""
        if from_user_id == to_user_id:
            raise ValidationError("Cannot relate a person to themselves")
        target = await self.users.get_by_id(to_user_id)
        if target is None:
            raise NotFound("Target user not found")
        existing = await self.relations.get_active_between(from_user_id, to_user_id, relation_type)
        if existing is not None:
            raise Conflict("Active relation already exists")
        try:
            return await self.relations.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                relation_type=relation_type,
                subjects=subjects,
                level=level,
                notes=notes,
                tags=tags,
                parent_rights=parent_rights,
            )
        except IntegrityError as e:
            await self.session.rollback()
            raise Conflict("Active relation already exists") from e

    def _build_relation_values(self, request: UpdateRelationRequest) -> dict:
        """Собирает изменяемые поля связи (только переданные)"""
        mapping = {
            UserRelation.subjects: request.subjects,
            UserRelation.level: request.level,
            UserRelation.notes: request.notes,
            UserRelation.tags: request.tags,
            UserRelation.status: request.status,
            UserRelation.start_date: request.start_date,
            UserRelation.end_date: request.end_date,
        }
        return {column: value for column, value in mapping.items() if value is not None}
