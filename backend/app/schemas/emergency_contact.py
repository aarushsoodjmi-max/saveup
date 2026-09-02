from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.auth import normalize_phone
from pydantic import field_validator


class EmergencyContactCreateRequest(BaseModel):
    contact_name: str = Field(min_length=1, max_length=100)
    relationship_label: str = Field(min_length=1, max_length=50)
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def _check_phone(cls, value: str) -> str:
        return normalize_phone(value)


class EmergencyContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_name: str
    relationship_label: str
    phone_number: str
    is_verified: bool
    created_at: datetime
