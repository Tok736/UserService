from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import TokenService
from src.exceptions import AccessDenied, AppException, NotFound, VersionConflict
from src.invitation.repository import InvitationRepository
from src.logger import logger
from src.rabbit import Response, err
from src.relation.repository import UserRelationRepository

from .models import User
from .repository import UserRepository
from .schemas import (
    DeleteProfileRequest,
    ReadProfileRequest,
    ReadRelatedProfileRequest,
    UpdateProfileRequest,
    UserRead,
)
from .utils import anonymized_profile_values


class UserService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        users: UserRepository,
        relations: UserRelationRepository,
        invitations: InvitationRepository,
        tokens: TokenService,
    ) -> None:
        self.session = session
        self.users = users
        self.relations = relations
        self.invitations = invitations
        self.tokens = tokens

    async def current_user(self, token: str) -> User:
        """Достаёт вызывающего из JWT и его профиль в UserService"""
        claims = self.tokens.decode(token)
        user = await self.users.get_by_user_id(claims.user_id)
        if user is None:
            logger.debug(f"[UserService] No profile for caller {claims.user_id}")
            raise NotFound("Profile not found")
        return user

    async def read_own_profile(self, request: ReadProfileRequest) -> Response[UserRead]:
        """Прочитать свой профиль"""
        try:
            user = await self.current_user(request.access_token)
        except AppException as exc:
            return err(exc.status, exc.message)
        return Response(data=UserRead.model_validate(user))

    async def read_related_profile(self, request: ReadRelatedProfileRequest) -> Response[UserRead]:
        """Прочитать профиль связанного человека с проверкой связи"""
        try:
            caller = await self.current_user(request.access_token)
            if request.target_user_row == caller.id:
                target = caller
            else:
                if not await self.relations.exists_link(caller.id, request.target_user_row):
                    logger.debug(f"[UserService] Caller {caller.id} has no link to {request.target_user_row}")
                    raise AccessDenied()
                target = await self.users.get_by_id(request.target_user_row)
                if target is None:
                    raise NotFound("Target profile not found")
        except AppException as exc:
            return err(exc.status, exc.message)
        return Response(data=UserRead.model_validate(target))

    async def update_own_profile(self, request: UpdateProfileRequest) -> Response[UserRead]:
        """Обновить свой профиль (оптимистичная блокировка)"""
        try:
            caller = await self.current_user(request.access_token)
            values = self._build_profile_values(request)
            if not values:
                return Response(data=UserRead.model_validate(caller))
            updated = await self.users.update(id=caller.id, version=request.version, values=values)
            if updated is None:
                logger.debug(f"[UserService] Version conflict updating profile {caller.id}")
                raise VersionConflict()
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(data=UserRead.model_validate(updated))

    async def delete_own_profile(self, request: DeleteProfileRequest) -> Response[UserRead]:
        """Удалить свой профиль: soft delete + анонимизация"""
        try:
            user = await self.current_user(request.access_token)
            updated = await self.users.soft_delete_by_id(id=user.id, anonymized=anonymized_profile_values())
            if updated is None:
                raise NotFound("Profile not found")
        except AppException as exc:
            return err(exc.status, exc.message)

        return Response(message="Profile deleted", data=UserRead.model_validate(updated))

    def _build_profile_values(self, request: UpdateProfileRequest) -> dict:
        """Собирает словарь изменяемых полей профиля (только переданные)"""
        mapping = {
            User.first_name: request.first_name,
            User.last_name: request.last_name,
            User.middle_name: request.middle_name,
            User.display_name: request.display_name,
            User.avatar_url: request.avatar_url,
            User.date_of_birth: request.date_of_birth,
            User.contacts: request.contacts,
            User.messengers: request.messengers,
            User.timezone: request.timezone,
            User.locale: request.locale,
            User.bio: request.bio,
            User.basic_role: request.basic_role,
        }
        return {column: value for column, value in mapping.items() if value is not None}
