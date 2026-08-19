from pydantic import BaseModel, ConfigDict

from app.models.enums import ThemePreference
from app.schemas.auth import UserPublic


class MeResponse(UserPublic):
    theme_preference: ThemePreference


class UserSettingsPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    theme_preference: ThemePreference


class UpdateSettingsRequest(BaseModel):
    theme_preference: ThemePreference
