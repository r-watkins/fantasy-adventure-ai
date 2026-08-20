from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SESSION_COOKIE_NAME
from app.db.session import get_db_session
from app.game.content_schemas import GameContent
from app.llm.mock_provider import MockNarrativeProvider
from app.llm.provider import NarrativeProvider
from app.models.session import UserSession
from app.models.user import User
from app.services.auth_service import get_valid_session


async def get_current_session(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> UserSession:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    session = await get_valid_session(db, token) if token is not None else None
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return session


async def get_current_user(
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    user = await db.get(User, session.user_id)
    # A valid session pointing at a missing/deactivated user shouldn't
    # happen (sessions cascade-delete with their user), but is_active can
    # go false without the session being revoked - treat both as 401.
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return user


def get_content(request: Request) -> GameContent:
    return request.app.state.content


def get_narrative_provider() -> NarrativeProvider:
    # Always the mock provider for now - Task 45 replaces this with a real
    # factory that switches on settings.llm_provider once
    # GeminiNarrativeProvider exists (Task 41).
    return MockNarrativeProvider()
