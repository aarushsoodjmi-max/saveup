from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WithdrawalRequestCreate(BaseModel):
    goal_id: UUID
    emergency_contact_id: UUID
    amount: Decimal = Field(gt=0, decimal_places=2)
    reason: str
    reason_notes: str | None = Field(default=None, max_length=500)

    @field_validator("reason")
    @classmethod
    def _check_reason(cls, value: str) -> str:
        allowed = {"MEDICAL", "FAMILY", "JOB_LOSS", "EDUCATION", "OTHER"}
        value = value.upper()
        if value not in allowed:
            raise ValueError(f"reason must be one of {sorted(allowed)}")
        return value


class WithdrawalApproveRequest(BaseModel):
    """Submitted by the emergency contact with the OTP they received."""

    otp: str

    @field_validator("otp")
    @classmethod
    def _check_otp(cls, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise ValueError("otp must be numeric")
        return value


class WithdrawalRejectRequest(BaseModel):
    """Submitted by the emergency contact, mirroring
    :class:`WithdrawalApproveRequest` but for a rejection, which also
    requires a short reason.
    """

    otp: str
    rejection_reason: str = Field(min_length=1, max_length=255)

    @field_validator("otp")
    @classmethod
    def _check_otp(cls, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise ValueError("otp must be numeric")
        return value


class WithdrawalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    goal_id: UUID
    emergency_contact_id: UUID
    amount: Decimal
    reason: str
    reason_notes: str | None
    status: str
    cooldown_ends_at: datetime | None
    rejection_reason: str | None
    requested_at: datetime
    approved_at: datetime | None
    completed_at: datetime | None
    # Only populated on the create-request response, and only outside
    # production (see settings.otp_debug_expose) -- lets the approval
    # flow be exercised end-to-end without a real SMS provider.
    debug_otp: str | None = None
