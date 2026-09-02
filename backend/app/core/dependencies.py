from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import Role
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import TokenError, TokenType, decode_token
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")

    try:
        payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Malformed token subject") from exc

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise ForbiddenError("Account is deactivated")

    return user


def require_roles(*allowed_roles: Role):
    """Dependency factory: ``Depends(require_roles(Role.ADMIN))``."""

    allowed_values = {role.value for role in allowed_roles}

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_values:
            raise ForbiddenError("You do not have permission to perform this action")
        return current_user

    return _dependency


require_admin = require_roles(Role.ADMIN)


class Pagination:
    def __init__(self, page: int = 1, limit: int = settings.default_page_size):
        self.page = max(page, 1)
        self.limit = min(max(limit, 1), settings.max_page_size)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def get_pagination(
    page: int = Query(1, ge=1),
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
) -> Pagination:
    return Pagination(page=page, limit=limit)


def get_idempotency_key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str | None:
    return idempotency_key
