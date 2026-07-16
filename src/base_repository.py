from collections.abc import AsyncGenerator
from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker


class BaseRepository:
    """
    Класс для работы с базой данных. Синтаксис использования:

    ```
    async with Repository() as db:
        ... = await db.some_method()
    ```
    """

    session: AsyncSession

    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session if session is not None else async_session_maker()  # type: ignore

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.session.close()

    @classmethod
    async def dependency(cls) -> AsyncGenerator[Self, None]:
        """Функция для использования с Depends"""
        async with cls() as db:
            yield db
