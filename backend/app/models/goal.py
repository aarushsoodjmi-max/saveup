from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.uuid_type import UUIDType

MONEY = Numeric(12, 2)


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="ck_goals_target_amount_positive"),
        CheckConstraint("saved_amount >= 0", name="ck_goals_saved_amount_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[str] = mapped_column(String(50), nullable=False)

    goal_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    target_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)

    # Source of truth for "how much is locked in this goal". Only ever
    # mutated by the ledger service inside a row-locked DB transaction.
    saved_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=Decimal("0.00"))

    monthly_target: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)

    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    lock_type: Mapped[str] = mapped_column(
        Enum("EASY", "MEDIUM", "HARD", name="goal_lock_type"),
        nullable=False,
        default="EASY",
    )

    status: Mapped[str] = mapped_column(
        Enum("ACTIVE", "PAUSED", "COMPLETED", "ARCHIVED", name="goal_status"),
        nullable=False,
        default="ACTIVE",
    )

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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

    @property
    def remaining_amount(self) -> Decimal:
        remaining = self.target_amount - self.saved_amount
        return remaining if remaining > 0 else Decimal("0.00")

    @property
    def progress_percentage(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        pct = (self.saved_amount / self.target_amount) * Decimal("100")
        return float(min(pct, Decimal("100")))
