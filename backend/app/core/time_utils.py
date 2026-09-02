"""Small helper for a recurring MySQL/SQLAlchemy gotcha.

MySQL has no ``TIMESTAMP WITH TIME ZONE`` type, so even though our
models declare ``DateTime(timezone=True)`` (so the ORM layer treats
values as UTC-aware in Python), values that round-trip through the
database come back **naive**. We always write UTC-aware datetimes, so
a naive value read back is safely assumed to already be UTC -- this
helper just re-attaches that tzinfo before comparing against
``datetime.now(timezone.utc)``.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
