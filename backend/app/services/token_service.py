"""Issues and rotates JWT access / opaque refresh token pairs."""

from datetime import timedelta

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, generate_refresh_token, hash_opaque_token
from app.core.time_utils import ensure_aware, utc_now
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPair


class TokenService:
    def __init__(self, refresh_token_repo: RefreshTokenRepository, user_repo: UserRepository | None = None):
        self.refresh_token_repo = refresh_token_repo
        # Only required by rotate(), which looks up the owning user from
        # the refresh token itself (the whole point of refresh is that
        # the caller does *not* have to present a still-valid access
        # token).
        self.user_repo = user_repo

    def issue_pair(self, user: User) -> TokenPair:
        access_token, _ = create_access_token(user.id, user.role)

        raw_refresh = generate_refresh_token()
        expires_at = utc_now() + timedelta(days=settings.refresh_token_expire_days)
        self.refresh_token_repo.create(
            user_id=user.id,
            token_hash=hash_opaque_token(raw_refresh),
            expires_at=expires_at,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def rotate(self, raw_refresh_token: str) -> TokenPair:
        """Validates the presented refresh token, revokes it, and issues
        a brand-new pair (rotation). The owning user is looked up from
        the refresh token record itself -- this endpoint is deliberately
        reachable without a valid access token, since a client's whole
        reason for calling it is that their access token has expired.

        Reusing an already-rotated-out token is treated as a compromise
        signal: the entire chain for that user is revoked so a stolen
        token can't be replayed after the legitimate client has already
        rotated past it.
        """
        if self.user_repo is None:
            raise RuntimeError("TokenService.rotate requires a user_repo")

        token_hash = hash_opaque_token(raw_refresh_token)
        stored = self.refresh_token_repo.get_by_hash(token_hash)

        if stored is None:
            raise UnauthorizedError("Invalid refresh token")

        if not stored.is_active or stored.revoked_at is not None:
            # Reuse of a revoked/rotated token: nuke the whole chain.
            self.refresh_token_repo.revoke_all_for_user(stored.user_id)
            raise UnauthorizedError("Refresh token has already been used; all sessions revoked")

        if stored.expires_at is not None and ensure_aware(stored.expires_at) < utc_now():
            raise UnauthorizedError("Refresh token has expired")

        user = self.user_repo.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account is unavailable")

        self.refresh_token_repo.revoke(stored)
        return self.issue_pair(user)

    def revoke(self, raw_refresh_token: str, user: User) -> None:
        token_hash = hash_opaque_token(raw_refresh_token)
        stored = self.refresh_token_repo.get_by_hash(token_hash)
        if stored is None or stored.user_id != user.id:
            # Logout is idempotent from the client's point of view.
            return
        self.refresh_token_repo.revoke(stored)
