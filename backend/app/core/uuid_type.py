from uuid import UUID

from sqlalchemy import BINARY
from sqlalchemy.types import TypeDecorator


class UUIDType(TypeDecorator):
    impl = BINARY(16)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        if isinstance(value, UUID):
            return value.bytes

        return UUID(value).bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return UUID(bytes=value)