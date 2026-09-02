from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.uuid_type import UUIDType

MONEY = Numeric(12, 2)


class Transaction(Base):
    """The unified, append-only financial ledger.

    Every deposit, withdrawal, and refund is recorded here exactly once.
    ``amount`` is always stored as a positive value; the sign/direction
    is implied by ``transaction_type``. ``idempotency_key`` carries a
    unique constraint so that retried requests (client timeout + retry,
    duplicate webhook delivery, etc.) can never be double-applied --
    the second insert attempt fails at the database level even if a
    race slips past an in-process check.

    Rows are never mutated after creation except for ``status``
    transitioning from PENDING to a terminal state (SUCCESS/FAILED) and,
    for a withdrawal later reversed, to REVERSED. Money movement into
    ``goals.saved_amount`` happens in the same DB transaction as the
    row's insert/terminal update, so the ledger and the goal balance can
    never drift apart.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
    )

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        Enum("DEPOSIT", "WITHDRAWAL", "REFUND", name="transaction_type"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum("PENDING", "SUCCESS", "FAILED", "REVERSED", name="transaction_status"),
        nullable=False,
        default="PENDING",
    )

    # Snapshot of goals.saved_amount immediately after this transaction
    # was applied. Purely an audit convenience; the goal row is always
    # the source of truth.
    balance_after: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)

    # Points at the originating PaymentOrder.id, WithdrawalRequest.id, or
    # (for a REFUND) the Transaction.id being refunded. Deliberately not
    # a foreign key -- the referenced table depends on transaction_type.
    reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reference_id: Mapped[UUID | None] = mapped_column(UUIDType, nullable=True)

    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
