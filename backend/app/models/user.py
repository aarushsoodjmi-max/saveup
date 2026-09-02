from datetime import date, datetime, timezone
from uuid import UUID, uuid4
from app.core.uuid_type import UUIDType
from sqlalchemy import Boolean, Date, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4,
    )

    phone_number: Mapped[str] = mapped_column(
        String(16),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(254),
        unique=True,
        nullable=True,
    )

    profile_picture: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    kyc_status: Mapped[str] = mapped_column(
        Enum("PENDING", "VERIFIED", "REJECTED"),
        default="PENDING",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        Enum("USER", "ADMIN", name="user_role"),
        default="USER",
        server_default="USER",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )