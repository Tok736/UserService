from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.relation.enums import RelationStatus, RelationType


# fmt: off
class UserRelation(Base):
    __tablename__ = "user_relation"

    id:            Mapped[int]             = mapped_column(primary_key=True)
    from_user_id:  Mapped[int]             = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    to_user_id:    Mapped[int]             = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[RelationType]    = mapped_column(SAEnum(RelationType, name="relation_type", values_callable=lambda e: [m.value for m in e]))
    subjects:      Mapped[list | None]     = mapped_column(JSONB)
    level:         Mapped[str | None]      = mapped_column(String(100))
    status:        Mapped[RelationStatus]  = mapped_column(SAEnum(RelationStatus, name="relation_status", values_callable=lambda e: [m.value for m in e]), server_default=RelationStatus.active.value, index=True)
    notes:         Mapped[str | None]      = mapped_column(Text)
    tags:          Mapped[list | None]     = mapped_column(JSONB)
    parent_rights: Mapped[dict | None]     = mapped_column(JSONB)
    start_date:    Mapped[date | None]     = mapped_column(Date)
    end_date:      Mapped[date | None]     = mapped_column(Date)
    deleted_at:    Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at:    Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    version:       Mapped[int]             = mapped_column(default=1, server_default="1")

    __table_args__ = (
        CheckConstraint("from_user_id <> to_user_id", name="ck_relation_no_self"),
        Index(
            "uq_active_relation",
            "from_user_id", "to_user_id", "relation_type",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_relation_from_type", "from_user_id", "relation_type"),
        Index("ix_relation_to", "to_user_id"),
    )
# fmt: on
