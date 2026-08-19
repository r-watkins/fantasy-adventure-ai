from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import generate_session_token, hash_password, hash_session_token
from app.db.session import create_engine, create_session_factory
from app.models.session import UserSession
from app.models.user import User
from app.services.auth_service import get_valid_session

pytestmark = pytest.mark.anyio


async def test_get_valid_session_rejects_expired_session(migrated_db_url: str) -> None:
    # Regression test: SQLite round-trips DateTime(timezone=True) columns as
    # naive, so comparing against datetime.now(UTC) directly raised
    # TypeError until get_valid_session started normalizing via
    # as_aware_utc(). This exercises the real DB round-trip, not just the
    # comparison in isolation, since the naive-vs-aware mismatch only shows
    # up after a value has actually gone through SQLite.
    engine = create_engine(migrated_db_url)
    session_factory = create_session_factory(engine)

    token = generate_session_token()
    async with session_factory() as db:
        user = User(email="expiry@example.com", password_hash=hash_password("whatever password"))
        db.add(user)
        await db.flush()
        db.add(
            UserSession(
                user_id=user.id,
                token_hash=hash_session_token(token),
                expires_at=datetime.now(UTC) - timedelta(days=1),
            )
        )
        await db.commit()

    async with session_factory() as db:
        result = await get_valid_session(db, token)

    assert result is None

    await engine.dispose()
