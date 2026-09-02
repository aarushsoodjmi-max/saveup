from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GoalCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    category: str = Field(min_length=1, max_length=50)
    goal_image: str | None = None
    target_amount: Decimal = Field(gt=0, decimal_places=2)
    monthly_target: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    deadline: date | None = None
    lock_type: str = "EASY"

    @field_validator("lock_type")
    @classmethod
    def _check_lock_type(cls, value: str) -> str:
        allowed = {"EASY", "MEDIUM", "HARD"}
        value = value.upper()
        if value not in allowed:
            raise ValueError(f"lock_type must be one of {sorted(allowed)}")
        return value

    @field_validator("deadline")
    @classmethod
    def _check_deadline(cls, value: date | None) -> date | None:
        if value is not None and value <= date.today():
            raise ValueError("deadline must be in the future")
        return value


class GoalUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    goal_image: str | None = None
    target_amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    monthly_target: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    deadline: date | None = None

    @field_validator("deadline")
    @classmethod
    def _check_deadline(cls, value: date | None) -> date | None:
        if value is not None and value <= date.today():
            raise ValueError("deadline must be in the future")
        return value


class GoalStatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _check_status(cls, value: str) -> str:
        allowed = {"ACTIVE", "PAUSED", "ARCHIVED"}
        value = value.upper()
        if value not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return value


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    description: str | None
    category: str
    goal_image: str | None
    target_amount: Decimal
    saved_amount: Decimal
    monthly_target: Decimal | None
    deadline: date | None
    lock_type: str
    status: str
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    remaining_amount: Decimal
    progress_percentage: float
