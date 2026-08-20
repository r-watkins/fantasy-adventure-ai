from pydantic import BaseModel

from app.models.enums import MessageRole

CURRENT_SCHEMA_VERSION = 1


class PlayerState(BaseModel):
    name: str
    origin_id: str
    origin_label: str
    location_id: str
    traits: list[str] = []


class InventoryEntry(BaseModel):
    item_id: str
    quantity: int
    equipped: bool = False


class CharacterState(BaseModel):
    relationship: str
    status: str
    memory: str


class Quest(BaseModel):
    quest_id: str
    status: str
    objective: str


class ContextMessage(BaseModel):
    role: MessageRole
    content: str


class GameState(BaseModel):
    schema_version: int = CURRENT_SCHEMA_VERSION
    turn_number: int = 0
    player: PlayerState
    inventory: list[InventoryEntry] = []
    characters: dict[str, CharacterState] = {}
    world_flags: dict[str, bool] = {}
    quests: list[Quest] = []
    story_summary: str = ""
    recent_context: list[ContextMessage] = []
