from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SESSION_COOKIE_NAME
from app.db.session import get_db_session
from app.models.session import UserSession
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
