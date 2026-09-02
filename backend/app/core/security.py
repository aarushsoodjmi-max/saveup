"""Security primitives: JWT access/refresh tokens, OTP hashing, and
opaque-token hashing for refresh-token storage.

Design notes
------------
- Access tokens are short-lived JWTs signed with HS256, carrying the
  user id (``sub``), role, and a token-type claim so they can never be
  mistaken for a refresh token even if replayed against the wrong
  endpoint.
- Refresh tokens are *opaque* high-entropy random strings, not JWTs.
  Only their SHA-256 hash is stored in the database (``refresh_tokens``
  table), so a leaked database dump does not hand out usable tokens.
- OTPs are hashed with HMAC-SHA256 using a server-side pepper before
  being stored in Redis, so a Redis dump alone does not reveal OTPs.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenError(Exception):
    """Raised for any invalid, expired, or malformed JWT."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: UUID, role: str) -> tuple[str, datetime]:
    expires_at = _now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": TokenType.ACCESS.value,
        "iat": _now(),
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except InvalidTokenError as exc:
        raise TokenError("Token is invalid") from exc

    if payload.get("type") != expected_type.value:
        raise TokenError(f"Expected a {expected_type.value} token")

    return payload


# --------------------------------------------------------------------
# Refresh tokens (opaque, stored hashed)
# --------------------------------------------------------------------

def generate_refresh_token() -> str:
    """A high-entropy, URL-safe opaque token (not a JWT)."""
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------
# OTP
# --------------------------------------------------------------------

def generate_otp(length: int | None = None) -> str:
    length = length or settings.otp_length
    upper_bound = 10**length
    value = secrets.randbelow(upper_bound)
    return str(value).zfill(length)


def hash_otp(phone_number: str, otp: str) -> str:
    """HMAC-SHA256(otp | phone_number) using a server-side pepper.

    Binding the phone number into the MAC prevents a stolen OTP hash for
    one phone number from being replayed against another.
    """
    message = f"{phone_number}:{otp}".encode("utf-8")
    key = settings.otp_hash_secret.encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_otp_hash(phone_number: str, otp: str, expected_hash: str) -> bool:
    candidate = hash_otp(phone_number, otp)
    return hmac.compare_digest(candidate, expected_hash)
