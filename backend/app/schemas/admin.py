from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class KYCUpdateRequest(BaseModel):
    kyc_status: str

    @field_validator("kyc_status")
    @classmethod
    def _check_status(cls, value: str) -> str:
        allowed = {"PENDING", "VERIFIED", "REJECTED"}
        value = value.upper()
        if value not in allowed:
            raise ValueError(f"kyc_status must be one of {sorted(allowed)}")
        return value


class AdminWithdrawalRejectRequest(BaseModel):
    """Admin override rejection -- no OTP required since the admin is
    already authenticated and RBAC-authorized, unlike the emergency
    contact's own reject call which must prove receipt of the OTP.
    """

    rejection_reason: str = Field(min_length=1, max_length=255)


class AdminUserResponse(BaseModel):
    id: UUID
    phone_number: str
    name: str
    email: str | None
    kyc_status: str
    role: str
    is_active: bool
    created_at: datetime
    total_saved: Decimal


class DashboardSummaryResponse(BaseModel):
    total_users: int
    active_users: int
    total_goals: int
    active_goals: int
    completed_goals: int
    total_saved_amount: Decimal
    total_withdrawn_amount: Decimal
    pending_kyc_count: int
    pending_withdrawal_count: int


class TransactionSearchParams(BaseModel):
    user_id: UUID | None = None
    goal_id: UUID | None = None
    transaction_type: str | None = None
    status: str | None = None
