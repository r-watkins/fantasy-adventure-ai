from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MessageRole


class CreateSaveRequest(BaseModel):
    origin_id: str
    # Both optional per design.md Task 26 ("optional character naming") -
    # slot_name labels the save in the save-select list, character_name is
    # the in-fiction player name embedded in game_state_json.player.name.
    character_name: str | None = Field(default=None, max_length=64)
    slot_name: str | None = Field(default=None, max_length=100)


class UpdateSaveRequest(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    archived: bool | None = None


class SaveSlotSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    origin_id: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class StoryMessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: MessageRole
    content: str
    turn_number: int
    created_at: datetime


class SaveSlotDetail(SaveSlotSummary):
    game_state_json: dict[str, Any]
    messages: list[StoryMessagePublic]
