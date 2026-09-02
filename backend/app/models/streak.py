from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.uuid_type import UUIDType


class Streak(Base):
    """One row per user, tracking consecutive deposit-days.

    Updated by ``StreakService`` every time a deposit succeeds: if the
    last saved date was yesterday, the streak extends; if it was today,
    it's a no-op (already counted); otherwise it resets to 1.
    """

    __tablename__ = "streaks"

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    best_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_saved_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
