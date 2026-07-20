import uuid
from datetime import date

from sqlalchemy import func, insert, select, update

from src.database import BaseRepository
from src.enums import AccountStatus, BasicRole
from src.user.models import User


class UserRepository(BaseRepository):
    """Доступ к таблице user"""

    async def get_by_id(self, id: int) -> User | None:
        """Профиль по внутреннему id"""
        return await self.session.scalar(select(User).where(User.id == id))

    async def get_by_user_id(self, user_id: uuid.UUID) -> User | None:
        """Профиль по Auth user_id"""
        return await self.session.scalar(select(User).where(User.user_id == user_id))

    async def create(
        self,
        *,
        user_id: uuid.UUID | None = None,
        basic_role: BasicRole = BasicRole.student,
        account_status: AccountStatus = AccountStatus.managed,
        email: str = "",
        first_name: str | None = None,
        last_name: str | None = None,
        middle_name: str | None = None,
        nickname: str | None = None,
        date_of_birth: date | None = None,
        contacts: dict | None = None,
        messengers: dict | None = None,
        timezone: str = "UTC",
        locale: str = "ru",
        bio: str | None = None,
    ) -> User:
        """Создать профиль (в т.ч. управляемую карточку без user_id)"""
        values = {
            User.user_id: user_id,
            User.basic_role: basic_role,
            User.account_status: account_status,
            User.email: email,
            User.first_name: first_name,
            User.last_name: last_name,
            User.middle_name: middle_name,
            User.nickname: nickname,
            User.date_of_birth: date_of_birth,
            User.contacts: contacts,
            User.messengers: messengers,
            User.timezone: timezone,
            User.locale: locale,
            User.bio: bio,
        }
        statement = insert(User).values(values).returning(User)
        user = await self.session.scalar(statement)
        await self.session.commit()
        return user

    async def update(self, *, id: int, version: int, values: dict) -> User | None:
        """Обновление с проверкой version; None при конфликте версий"""
        values = {**values, User.version: User.version + 1}
        statement = update(User).where(User.id == id, User.version == version).values(values).returning(User)
        user = await self.session.scalar(statement)
        await self.session.commit()
        return user

    async def set_account_status(self, *, user_id: uuid.UUID, status: AccountStatus) -> User | None:
        """Обновить account_status по Auth user_id (для событий Auth)"""
        statement = (
            update(User)
            .where(User.user_id == user_id)
            .values({User.account_status: status, User.version: User.version + 1})
            .returning(User)
        )
        user = await self.session.scalar(statement)
        await self.session.commit()
        return user

    async def activate_card(self, *, id: int, user_id: uuid.UUID) -> User | None:
        """Проставить user_id и перевести карточку в active (идемпотентно)"""
        statement = (
            update(User)
            .where(User.id == id)
            .values(
                {
                    User.user_id: user_id,
                    User.account_status: AccountStatus.active,
                    User.version: User.version + 1,
                }
            )
            .returning(User)
        )
        user = await self.session.scalar(statement)
        await self.session.commit()
        return user

    async def mark_invited(self, *, id: int) -> User | None:
        """Перевести управляемую карточку в статус invited"""
        statement = (
            update(User)
            .where(User.id == id)
            .values({User.account_status: AccountStatus.invited, User.version: User.version + 1})
            .returning(User)
        )
        user = await self.session.scalar(statement)
        await self.session.commit()
        return user

    async def set_consent(self, *, id: int, consent: dict) -> User | None:
        """Зафиксировать согласие на обработку ПД (в т.ч. родительское)"""
        statement = (
            update(User)
            .where(User.id == id)
            .values({User.consent: consent, User.version: User.version + 1})
            .returning(User)
        )
        user = await self.session.scalar(statement)
        await self.session.commit()
        return user

    async def soft_delete(self, *, user_id: uuid.UUID, anonymized: dict) -> User | None:
        """Soft delete + анонимизация ПД по Auth user_id"""
        values = {
            **anonymized,
            User.account_status: AccountStatus.deleted,
            User.deleted_at: func.now(),
            User.version: User.version + 1,
        }
        statement = update(User).where(User.user_id == user_id).values(values).returning(User)
        user = await self.session.scalar(statement)
        await self.session.commit()
        return user

    async def soft_delete_by_id(self, *, id: int, anonymized: dict) -> User | None:
        """Soft delete + анонимизация ПД по внутреннему id"""
        values = {
            **anonymized,
            User.account_status: AccountStatus.deleted,
            User.deleted_at: func.now(),
            User.version: User.version + 1,
        }
        statement = update(User).where(User.id == id).values(values).returning(User)
        user = await self.session.scalar(statement)
        await self.session.commit()
        return user
