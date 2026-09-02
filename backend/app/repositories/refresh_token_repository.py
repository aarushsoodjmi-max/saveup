from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time_utils import utc_now
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, user_id: UUID, token_hash: str, expires_at) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(token)
        self.db.flush()
        return token

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke(self, token: RefreshToken) -> None:
        token.revoked_at = utc_now()
        token.is_active = False
        self.db.flush()

    def revoke_all_for_user(self, user_id: UUID) -> None:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_active.is_(True),
        )
        for token in self.db.execute(stmt).scalars().all():
            token.revoked_at = utc_now()
            token.is_active = False
        self.db.flush()
