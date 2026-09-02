from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.uuid_type import UUIDType


class Achievement(Base):
    """Master, admin-curated list of achievements users can unlock."""

    __tablename__ = "achievements"

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    title: Mapped[str] = mapped_column(String(100), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    badge_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    metric: Mapped[str] = mapped_column(
        Enum("TOTAL_SAVED", "STREAK_DAYS", "GOALS_COMPLETED", name="achievement_metric"),
        nullable=False,
    )

    required_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UserAchievement(Base):
    """An achievement a specific user has unlocked (once, ever)."""

    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    achievement_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
