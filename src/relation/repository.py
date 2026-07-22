from sqlalchemy import Select, String, and_, func, insert, or_, select, update

from src.database import BaseRepository
from src.relation.enums import RelationStatus, RelationType
from src.relation.models import UserRelation
from src.relation.schemas import StudentSort
from src.user.models import User


class UserRelationRepository(BaseRepository):
    """Доступ к таблице user_relation"""

    async def get_by_id(self, id: int) -> UserRelation | None:
        return await self.session.scalar(select(UserRelation).where(UserRelation.id == id))

    async def get_active_between(
        self, from_user_id: int, to_user_id: int, relation_type: RelationType
    ) -> UserRelation | None:
        statement = select(UserRelation).where(
            UserRelation.from_user_id == from_user_id,
            UserRelation.to_user_id == to_user_id,
            UserRelation.relation_type == relation_type,
            UserRelation.status == RelationStatus.active,
        )
        return await self.session.scalar(statement)

    async def exists_link(self, a_row: int, b_row: int) -> bool:
        """Есть ли живая связь между двумя людьми в любом направлении (доменная изоляция)"""
        statement = select(UserRelation.id).where(
            UserRelation.deleted_at.is_(None),
            or_(
                and_(UserRelation.from_user_id == a_row, UserRelation.to_user_id == b_row),
                and_(UserRelation.from_user_id == b_row, UserRelation.to_user_id == a_row),
            ),
        )
        return await self.session.scalar(statement) is not None

    async def create(
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
        """Создать связь"""
        values = {
            UserRelation.from_user_id: from_user_id,
            UserRelation.to_user_id: to_user_id,
            UserRelation.relation_type: relation_type,
            UserRelation.subjects: subjects,
            UserRelation.level: level,
            UserRelation.notes: notes,
            UserRelation.tags: tags,
            UserRelation.parent_rights: parent_rights,
        }
        statement = insert(UserRelation).values(values).returning(UserRelation)
        relation = await self.session.scalar(statement)
        await self.session.commit()
        return relation

    async def update(self, *, id: int, version: int, values: dict) -> UserRelation | None:
        """Обновление с проверкой version; None при конфликте версий"""
        values = {**values, UserRelation.version: UserRelation.version + 1}
        statement = (
            update(UserRelation)
            .where(UserRelation.id == id, UserRelation.version == version)
            .values(values)
            .returning(UserRelation)
        )
        relation = await self.session.scalar(statement)
        await self.session.commit()
        return relation

    async def soft_delete(self, *, id: int, version: int) -> UserRelation | None:
        """Мягкое удаление связи (deleted_at + archived)"""
        values = {
            UserRelation.deleted_at: func.now(),
            UserRelation.status: RelationStatus.archived,
            UserRelation.version: UserRelation.version + 1,
        }
        statement = (
            update(UserRelation)
            .where(UserRelation.id == id, UserRelation.version == version)
            .values(values)
            .returning(UserRelation)
        )
        relation = await self.session.scalar(statement)
        await self.session.commit()
        return relation

    def _apply_student_filters(
        self,
        statement: Select,
        *,
        status: RelationStatus | None,
        subject: str | None,
        tag: str | None,
        group_id: int | None,
        search: str | None,
    ):
        """Навешивает общие фильтры на список учеников"""
        statement = statement.where(UserRelation.deleted_at.is_(None))
        if status is not None:
            statement = statement.where(UserRelation.status == status)
        if subject is not None:
            statement = statement.where(UserRelation.subjects.contains([subject]))
        if tag is not None:
            statement = statement.where(UserRelation.tags.contains([tag]))
        # if group_row is not None:
        #     member_subq = (
        #         select(GroupMembership.user_id)
        #         .where(GroupMembership.group_id == group_row, GroupMembership.deleted_at.is_(None))
        #         .scalar_subquery()
        #     )
        #     statement = statement.where(UserRelation.to_user_id.in_(member_subq))
        if search is not None:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.nickname.ilike(pattern),
                    func.cast(User.contacts, String).ilike(pattern),
                )
            )
        return statement

    async def list_students(
        self,
        *,
        from_user_id: int,
        offset: int,
        limit: int,
        status: RelationStatus | None = None,
        subject: str | None = None,
        tag: str | None = None,
        group_row: int | None = None,
        search: str | None = None,
        sort: StudentSort = StudentSort.created,
        descending: bool = True,
    ) -> tuple[list[tuple[UserRelation, User]], int]:
        """Ученики репетитора (from_user = я, relation_type = tutor_of) + их профили"""
        base = (
            select(UserRelation, User)
            .join(User, User.id == UserRelation.to_user_id)
            .where(
                UserRelation.from_user_id == from_user_id,
                UserRelation.relation_type == RelationType.tutor_of,
            )
        )
        base = self._apply_student_filters(
            base, status=status, subject=subject, tag=tag, group_id=group_row, search=search
        )

        count_statement = select(func.count()).select_from(base.subquery())
        total = await self.session.scalar(count_statement) or 0

        sort_column = User.nickname if sort == StudentSort.name_ else UserRelation.created_at
        base = base.order_by(sort_column.desc() if descending else sort_column.asc())
        base = base.offset(offset).limit(limit)

        rows = (await self.session.execute(base)).all()
        return [(row[0], row[1]) for row in rows], total

    async def list_tutors(
        self, *, to_user_id: int, offset: int, limit: int
    ) -> tuple[list[tuple[UserRelation, User]], int]:
        """Репетиторы человека (to_user = я, relation_type = tutor_of) + их профили"""
        base = (
            select(UserRelation, User)
            .join(User, User.id == UserRelation.from_user_id)
            .where(
                UserRelation.to_user_id == to_user_id,
                UserRelation.relation_type == RelationType.tutor_of,
                UserRelation.deleted_at.is_(None),
            )
        )
        count_statement = select(func.count()).select_from(base.subquery())
        total = await self.session.scalar(count_statement) or 0

        base = base.order_by(UserRelation.created_at.desc()).offset(offset).limit(limit)
        rows = (await self.session.execute(base)).all()
        return [(row[0], row[1]) for row in rows], total
