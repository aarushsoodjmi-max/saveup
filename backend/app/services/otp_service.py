"""OTP issuance and verification, backed entirely by Redis.

Storage shape per phone number, key ``otp:{phone_number}``:
    {"hash": "<hmac-sha256 hex>", "attempts": <int>}
TTL on the key enforces expiry -- there is no separate "expired" state
to clean up, Redis does it for us.

A short-lived sibling key ``otp:cooldown:{phone_number}`` enforces the
resend cooldown independently of the OTP's own TTL, so a user can't
immediately request a fresh OTP to reset their attempt counter.
"""

import json

import redis

from app.core.config import settings
from app.core.exceptions import InvalidOTPError, OTPExpiredError, RateLimitedError
from app.core.security import generate_otp, hash_otp, verify_otp_hash
from app.services.sms_provider import SMSProvider


class OTPService:
    def __init__(self, redis_client: redis.Redis, provider: SMSProvider):
        self.redis = redis_client
        self.provider = provider

    @staticmethod
    def _otp_key(phone_number: str) -> str:
        return f"otp:{phone_number}"

    @staticmethod
    def _cooldown_key(phone_number: str) -> str:
        return f"otp:cooldown:{phone_number}"

    def send_otp(self, phone_number: str) -> tuple[int, int, str | None]:
        """Generates, stores, and "sends" an OTP.

        Returns ``(expires_in_seconds, resend_cooldown_seconds, debug_otp)``.
        ``debug_otp`` is only non-None when ``settings.otp_debug_expose``
        is on (never in production), so integration tests and local
        development can proceed without a real SMS provider.
        """
        cooldown_key = self._cooldown_key(phone_number)
        if self.redis.exists(cooldown_key):
            ttl = self.redis.ttl(cooldown_key)
            raise RateLimitedError(
                "Please wait before requesting another OTP",
                details={"retry_after_seconds": ttl if ttl and ttl > 0 else settings.otp_resend_cooldown_seconds},
            )

        otp = generate_otp()
        payload = {"hash": hash_otp(phone_number, otp), "attempts": 0}

        otp_key = self._otp_key(phone_number)
        self.redis.set(otp_key, json.dumps(payload), ex=settings.otp_expire_seconds)
        if settings.otp_resend_cooldown_seconds > 0:
            self.redis.set(cooldown_key, "1", ex=settings.otp_resend_cooldown_seconds)

        self.provider.send(phone_number, f"Your SaveUp verification code is {otp}")

        debug_otp = otp if (settings.otp_debug_expose and not settings.is_production) else None
        return settings.otp_expire_seconds, settings.otp_resend_cooldown_seconds, debug_otp

    def verify_otp(self, phone_number: str, otp: str) -> None:
        """Raises on failure; returns None (and consumes the OTP) on success."""
        otp_key = self._otp_key(phone_number)
        raw = self.redis.get(otp_key)
        if raw is None:
            raise OTPExpiredError("OTP has expired or was never requested")

        payload = json.loads(raw)

        if payload["attempts"] >= settings.otp_max_attempts:
            self.redis.delete(otp_key)
            raise InvalidOTPError("Too many incorrect attempts, please request a new OTP")

        if not verify_otp_hash(phone_number, otp, payload["hash"]):
            payload["attempts"] += 1
            ttl = self.redis.ttl(otp_key)
            self.redis.set(otp_key, json.dumps(payload), ex=ttl if ttl and ttl > 0 else settings.otp_expire_seconds)
            raise InvalidOTPError("Incorrect OTP")

        # One-time use: consume it immediately on success. Also clear the
        # resend cooldown -- it exists to stop OTP-request spam before a
        # code is ever used, not to lock a user out of a fresh login
        # shortly after a successful one. Without this, a second
        # legitimate send-otp call (e.g. logging in again a minute
        # later) would be wrongly rate-limited by the cooldown left over
        # from the first, already-completed login.
        self.redis.delete(otp_key)
        self.redis.delete(self._cooldown_key(phone_number))
