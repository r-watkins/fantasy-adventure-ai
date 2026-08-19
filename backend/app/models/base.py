import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_aware_utc(value: datetime) -> datetime:
    # SQLite has no native timezone-aware datetime type: SQLAlchemy's
    # DateTime(timezone=True) still round-trips values as naive on this
    # dialect, so anything read back from the DB needs re-tagging as UTC
    # before comparing against a tz-aware datetime.now(UTC).
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
