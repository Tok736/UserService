import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.enums import AccountStatus, BasicRole


# fmt: off
class User(Base):
    """Профиль любого человека: репетитора, ученика или родителя"""
    __tablename__ = "user"

    id:             Mapped[int]                = mapped_column(primary_key=True)
    user_id:        Mapped[uuid.UUID | None]   = mapped_column(PgUUID(as_uuid=True), unique=True, index=True, nullable=True)
    basic_role:     Mapped[BasicRole]          = mapped_column(SAEnum(BasicRole, name="basic_role", values_callable=lambda e: [m.value for m in e]), server_default=BasicRole.student.value)
    account_status: Mapped[AccountStatus]      = mapped_column(SAEnum(AccountStatus, name="account_status", values_callable=lambda e: [m.value for m in e]), server_default=AccountStatus.managed.value, index=True)
    first_name:     Mapped[str | None]         = mapped_column(String(100))
    last_name:      Mapped[str | None]         = mapped_column(String(100))
    middle_name:    Mapped[str | None]         = mapped_column(String(100))
    display_name:   Mapped[str | None]         = mapped_column(String(200))
    avatar_url:     Mapped[str | None]         = mapped_column(String(512))
    date_of_birth:  Mapped[date | None]        = mapped_column(Date)
    contacts:       Mapped[dict | None]        = mapped_column(JSONB)
    messengers:     Mapped[dict | None]        = mapped_column(JSONB)
    timezone:       Mapped[str]                = mapped_column(String(64), server_default="UTC")
    locale:         Mapped[str]                = mapped_column(String(16), server_default="ru")
    bio:            Mapped[str | None]         = mapped_column(Text)
    consent:        Mapped[dict | None]        = mapped_column(JSONB)
    deleted_at:     Mapped[datetime | None]    = mapped_column(DateTime(timezone=True))
    created_at:     Mapped[datetime]           = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:     Mapped[datetime]           = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    version:        Mapped[int]                = mapped_column(default=1, server_default="1")
# fmt: on
