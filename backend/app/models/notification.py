from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.uuid_type import UUIDType


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)

    type: Mapped[str] = mapped_column(
        Enum(
            "REMINDER",
            "GOAL",
            "PAYMENT",
            "SYSTEM",
            "ACHIEVEMENT",
            "WITHDRAWAL",
            name="notification_type",
        ),
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
