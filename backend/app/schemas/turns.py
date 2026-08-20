from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MessageRole


class SubmitTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class TurnMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: MessageRole
    content: str


class TurnResponse(BaseModel):
    player_message: TurnMessage
    narrator_message: TurnMessage
    game_state: dict[str, Any]
    turn_number: int
