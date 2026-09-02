from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.uuid_type import UUIDType


class RefreshToken(Base):
    """Stores only the SHA-256 hash of each issued refresh token.

    Supports rotation (``replaced_by_id``) and revocation (``revoked_at``)
    so that reusing a rotated-out token can be detected and treated as a
    signal to revoke the entire chain.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    replaced_by_id: Mapped[UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
