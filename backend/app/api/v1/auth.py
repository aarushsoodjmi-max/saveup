from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.core.redis import get_redis
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    LogoutRequest,
    RefreshTokenRequest,
    SendOTPRequest,
    SendOTPResponse,
    TokenPair,
    VerifyOTPRequest,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService
from app.services.rate_limit_service import RateLimitService
from app.services.sms_provider import sms_provider
from app.services.token_service import TokenService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/send-otp", response_model=SendOTPResponse)
def send_otp(payload: SendOTPRequest, redis_client=Depends(get_redis)):
    RateLimitService(redis_client).hit(
        f"otp_send:{payload.phone_number}",
        limit=settings.rate_limit_otp_per_hour,
        window_seconds=3600,
    )
    otp_service = OTPService(redis_client, provider=sms_provider)
    expires_in, resend_in, debug_otp = otp_service.send_otp(payload.phone_number)
    return SendOTPResponse(
        message="OTP sent successfully",
        otp_expires_in_seconds=expires_in,
        resend_available_in_seconds=resend_in,
        debug_otp=debug_otp,
    )


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(payload: VerifyOTPRequest, db=Depends(get_db), redis_client=Depends(get_redis)):
    RateLimitService(redis_client).hit(
        f"otp_verify:{payload.phone_number}",
        limit=settings.rate_limit_login_per_hour,
        window_seconds=3600,
    )
    otp_service = OTPService(redis_client, provider=sms_provider)
    auth_service = AuthService(db, otp_service)
    return auth_service.verify_otp_and_authenticate(payload.phone_number, payload.otp, payload.name)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(payload: RefreshTokenRequest, db=Depends(get_db)):
    """Deliberately does not require a valid access token -- that's the
    whole point of a refresh call. The presented refresh token itself
    (validated + rotated inside ``TokenService``) is the credential.
    """
    token_service = TokenService(RefreshTokenRepository(db), UserRepository(db))
    pair = token_service.rotate(payload.refresh_token)
    db.commit()
    return pair


@router.post("/logout", response_model=MessageResponse)
def logout(payload: LogoutRequest, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    token_service = TokenService(RefreshTokenRepository(db))
    token_service.revoke(payload.refresh_token, current_user)
    db.commit()
    return MessageResponse(message="Logged out successfully")
