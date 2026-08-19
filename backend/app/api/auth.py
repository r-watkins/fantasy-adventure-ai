from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import set_session_cookie
from app.db.session import get_db_session
from app.schemas.auth import RegisterRequest, UserPublic
from app.services.auth_service import EmailAlreadyRegisteredError, register_user

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
