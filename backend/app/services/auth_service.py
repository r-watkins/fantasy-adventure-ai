from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    session_expires_at,
)
from app.models.session import UserSession
from app.models.user import User
from app.models.user_settings import UserSettings


class EmailAlreadyRegisteredError(Exception):
    pass


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

    token = generate_session_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=session_expires_at(),
        )
    )

    return user, token
