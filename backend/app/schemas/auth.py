import re

from pydantic import BaseModel, field_validator

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")


def normalize_phone(value: str) -> str:
    value = value.strip()
    if not PHONE_REGEX.match(value):
        raise ValueError("phone_number must be a valid E.164-style number, e.g. +919876543210")
    return value


class SendOTPRequest(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def _check_phone(cls, value: str) -> str:
        return normalize_phone(value)


class SendOTPResponse(BaseModel):
    message: str
    otp_expires_in_seconds: int
    resend_available_in_seconds: int
    # Only populated outside production (settings.otp_debug_expose=True)
    # so the API can be exercised end-to-end without a real SMS provider.
    debug_otp: str | None = None


class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp: str
    # Required only for brand-new phone numbers (first-time registration).
    name: str | None = None

    @field_validator("phone_number")
    @classmethod
    def _check_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("otp")
    @classmethod
    def _check_otp(cls, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise ValueError("otp must be numeric")
        return value


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenPair):
    is_new_user: bool


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
