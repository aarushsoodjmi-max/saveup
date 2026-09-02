"""Shared enumerations used across models, schemas, and services.

These mirror the string values stored in the database ``Enum`` columns.
Keeping them centralized avoids magic strings scattered through the
service layer and gives Pydantic schemas a single source of truth.
"""

from enum import Enum


class Role(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class KYCStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class GoalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class LockType(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    REFUND = "REFUND"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class WithdrawalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COOLDOWN = "COOLDOWN"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WithdrawalReason(str, Enum):
    MEDICAL = "MEDICAL"
    FAMILY = "FAMILY"
    JOB_LOSS = "JOB_LOSS"
    EDUCATION = "EDUCATION"
    OTHER = "OTHER"


class PaymentOrderStatus(str, Enum):
    CREATED = "CREATED"
    ATTEMPTED = "ATTEMPTED"
    PAID = "PAID"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class PaymentAttemptStatus(str, Enum):
    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class NotificationType(str, Enum):
    REMINDER = "REMINDER"
    GOAL = "GOAL"
    PAYMENT = "PAYMENT"
    SYSTEM = "SYSTEM"
    ACHIEVEMENT = "ACHIEVEMENT"
    WITHDRAWAL = "WITHDRAWAL"


class AchievementMetric(str, Enum):
    TOTAL_SAVED = "TOTAL_SAVED"
    STREAK_DAYS = "STREAK_DAYS"
    GOALS_COMPLETED = "GOALS_COMPLETED"


# Lock type -> cooling-off period (hours) applied to emergency withdrawals.
# EASY has no cooldown (only emergency contact approval is required).
LOCK_TYPE_COOLDOWN_HOURS: dict[str, int] = {
    LockType.EASY.value: 0,
    LockType.MEDIUM.value: 24,
    LockType.HARD.value: 72,
}

# Lock types for which an approved-but-not-yet-completed withdrawal can
# still be cancelled by the user. HARD lock withdrawals become
# irreversible the moment the emergency contact approves them.
LOCK_TYPES_CANCELLABLE_AFTER_APPROVAL = {LockType.EASY.value, LockType.MEDIUM.value}
