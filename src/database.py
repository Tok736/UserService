from collections.abc import AsyncGenerator

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
