from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone_number: str
    name: str
    email: str | None
    profile_picture: str | None
    date_of_birth: date | None
    kyc_status: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    profile_picture: str | None = None
    date_of_birth: date | None = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not (1 <= len(value) <= 100):
            raise ValueError("name must be between 1 and 100 characters")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def _check_dob(cls, value: date | None) -> date | None:
        if value is None:
            return value
        if value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        age_years = (date.today() - value).days / 365.25
        if age_years < 18:
            raise ValueError("must be at least 18 years old")
        return value
