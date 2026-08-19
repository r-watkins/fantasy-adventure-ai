from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_session
from app.core.config import get_settings
from app.core.security import clear_session_cookie, set_session_cookie
from app.db.session import get_db_session
from app.models.session import UserSession
from app.schemas.auth import LoginRequest, RegisterRequest, UserPublic
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    create_session,
    register_user,
    revoke_session,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> UserPublic:
    try:
        user, token = await register_user(db, body.email, body.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Email is already registered"
        ) from exc

    settings = get_settings()
    set_session_cookie(response, token, secure=settings.environment == "production")

    return UserPublic.model_validate(user)


@router.post("/login", response_model=UserPublic)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> UserPublic:
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = await create_session(db, user.id)

    settings = get_settings()
    set_session_cookie(response, token, secure=settings.environment == "production")

    return UserPublic.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: UserSession = Depends(get_current_session),
) -> None:
    revoke_session(session)

    settings = get_settings()
    clear_session_cookie(response, secure=settings.environment == "production")
