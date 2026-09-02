from sqlalchemy.orm import Session

from app.core.exceptions import ValidationAppError
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse
from app.services.otp_service import OTPService
from app.services.token_service import TokenService


class AuthService:
    def __init__(self, db: Session, otp_service: OTPService):
        self.db = db
        self.otp_service = otp_service
        self.user_repo = UserRepository(db)
        self.token_service = TokenService(RefreshTokenRepository(db))

    def send_otp(self, phone_number: str) -> tuple[int, int, str | None]:
        return self.otp_service.send_otp(phone_number)

    def verify_otp_and_authenticate(self, phone_number: str, otp: str, name: str | None) -> AuthResponse:
        self.otp_service.verify_otp(phone_number, otp)

        user = self.user_repo.get_by_phone(phone_number)
        is_new_user = user is None

        if is_new_user:
            if not name or not name.strip():
                raise ValidationAppError("name is required for first-time registration")
            user = self.user_repo.create(phone_number=phone_number, name=name.strip())

        pair = self.token_service.issue_pair(user)
        self.db.commit()

        return AuthResponse(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            expires_in=pair.expires_in,
            is_new_user=is_new_user,
        )
