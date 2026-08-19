from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.me import MeResponse, UpdateSettingsRequest, UserSettingsPublic

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    # Always exists: register_user creates it atomically with the user.
    settings_row = await db.get(UserSettings, user.id)
    return MeResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        theme_preference=settings_row.theme_preference,
    )


@router.put("/me/settings", response_model=UserSettingsPublic)
async def update_settings(
    body: UpdateSettingsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserSettingsPublic:
    settings_row = await db.get(UserSettings, user.id)
    settings_row.theme_preference = body.theme_preference
    return UserSettingsPublic.model_validate(settings_row)
