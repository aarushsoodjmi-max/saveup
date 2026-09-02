from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.uuid_type import UUIDType

MONEY = Numeric(12, 2)


class PaymentOrder(Base):
    """A deposit intent created before money actually moves.

    Mirrors the "create order, then verify/webhook" shape used by real
    payment gateways (Razorpay, Stripe, etc.) so swapping the mock
    provider for a real one later only touches
    ``app.services.payment_service``.
    """

    __tablename__ = "payment_orders"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_orders_amount_positive"),
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

    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    provider: Mapped[str] = mapped_column(String(30), nullable=False, default="mock")

    provider_order_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum("CREATED", "ATTEMPTED", "PAID", "FAILED", "EXPIRED", name="payment_order_status"),
        nullable=False,
        default="CREATED",
    )

    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    # Set once a successful PaymentAttempt has produced a ledger entry,
    # so the webhook handler can short-circuit duplicate deliveries
    # without re-inspecting the whole attempt history.
    transaction_id: Mapped[UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
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


class PaymentAttempt(Base):
    """One attempt (webhook delivery or client verify call) against an order.

    A single :class:`PaymentOrder` can have multiple attempts (retry
    after failure, duplicate webhook redelivery); only the first
    SUCCESS attempt is allowed to move money.
    """

    __tablename__ = "payment_attempts"

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)

    payment_order_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("payment_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    status: Mapped[str] = mapped_column(
        Enum("INITIATED", "SUCCESS", "FAILED", name="payment_attempt_status"),
        nullable=False,
        default="INITIATED",
    )

    signature: Mapped[str | None] = mapped_column(String(255), nullable=True)

    signature_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
