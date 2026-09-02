from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.uuid_type import UUIDType

MONEY = Numeric(12, 2)


class WithdrawalRequest(Base):
    """Emergency withdrawal workflow state machine.

    PENDING -> APPROVED -> (COOLDOWN if applicable) -> COMPLETED
             -> REJECTED
    PENDING/APPROVED(*) -> CANCELLED  (* only for EASY/MEDIUM locks)
    APPROVED/COOLDOWN -> FAILED       (money release failed)
    """

    __tablename__ = "withdrawal_requests"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_withdrawal_requests_amount_positive"),
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

    emergency_contact_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("emergency_contacts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)

    reason: Mapped[str] = mapped_column(
        Enum("MEDICAL", "FAMILY", "JOB_LOSS", "EDUCATION", "OTHER", name="withdrawal_reason"),
        nullable=False,
    )

    reason_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(
            "PENDING",
            "APPROVED",
            "REJECTED",
            "COOLDOWN",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
            name="withdrawal_status",
        ),
        nullable=False,
        default="PENDING",
    )

    # OTP sent to the emergency contact to approve the request. Hashed
    # the same way login OTPs are (HMAC-SHA256 with a server pepper).
    otp_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    otp_attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    cooldown_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    transaction_id: Mapped[UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
