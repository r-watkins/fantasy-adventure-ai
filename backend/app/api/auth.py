from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_session
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import (
    clear_legacy_session_cookie,
    clear_session_cookie,
    set_session_cookie,
)
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


def _issue_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    secure = settings.environment == "production"
    set_session_cookie(response, token, secure=secure, path=settings.session_cookie_path)
    if settings.session_cookie_path != "/":
        # See clear_legacy_session_cookie: a leftover Path=/ cookie would
        # otherwise shadow the freshly scoped one.
        clear_legacy_session_cookie(response, secure=secure)


def _remove_session_cookie(response: Response) -> None:
    settings = get_settings()
    secure = settings.environment == "production"
    clear_session_cookie(response, secure=secure, path=settings.session_cookie_path)
    if settings.session_cookie_path != "/":
        clear_legacy_session_cookie(response, secure=secure)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register(
    request: Request,
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

    _issue_session_cookie(response, token)

    return UserPublic.model_validate(user)


@router.post("/login", response_model=UserPublic)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> UserPublic:
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = await create_session(db, user.id)

    _issue_session_cookie(response, token)

    return UserPublic.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: UserSession = Depends(get_current_session),
) -> None:
    revoke_session(session)

    _remove_session_cookie(response)
