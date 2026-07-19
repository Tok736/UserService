from collections.abc import AsyncGenerator
from typing import Any, Self

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import settings

metadata = MetaData()
Base: DeclarativeMeta = declarative_base(metadata=metadata)

engine = create_async_engine(settings.sql.sqlalchemy_url)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Функция для выдачи асинхронного соединения с базой данных"""

    async with async_session_maker() as session:  # pyright: ignore[reportGeneralTypeIssues]
        yield session


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
