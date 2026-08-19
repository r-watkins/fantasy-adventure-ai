from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    needs_rehash,
    session_expires_at,
    verify_password,
)
from app.models.base import as_aware_utc
from app.models.session import UserSession
from app.models.user import User
from app.models.user_settings import UserSettings


class EmailAlreadyRegisteredError(Exception):
    pass


async def create_session(db: AsyncSession, user_id: str) -> str:
    token = generate_session_token()
    db.add(
        UserSession(
            user_id=user_id,
            token_hash=hash_session_token(token),
            expires_at=session_expires_at(),
        )
    )
    return token


async def register_user(db: AsyncSession, email: str, password: str) -> tuple[User, str]:
    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise EmailAlreadyRegisteredError()

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        # Flush (not commit - the get_db_session dependency commits at the
        # end of the request) to populate user.id and surface a race on the
        # unique email index as IntegrityError rather than a generic 500.
        await db.flush()
    except IntegrityError as exc:
        raise EmailAlreadyRegisteredError() from exc

    db.add(UserSettings(user_id=user.id))
    token = await create_session(db, user.id)

    return user, token


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    # Returns None for both "no such user" and "wrong password" - callers
    # must surface one generic error either way, to avoid account
    # enumeration via response differences.
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    return user


async def get_valid_session(db: AsyncSession, token: str) -> UserSession | None:
    session = await db.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(token))
    )
    if session is None:
        return None
    if session.revoked_at is not None:
        return None
    if as_aware_utc(session.expires_at) <= datetime.now(UTC):
        return None
    return session


def revoke_session(session: UserSession) -> None:
    session.revoked_at = datetime.now(UTC)
