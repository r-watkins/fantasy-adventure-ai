from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.content_schemas import GameContent, Origin
from app.models.base import utcnow
from app.models.enums import MessageRole
from app.models.save_slot import SaveSlot
from app.models.story_message import StoryMessage


class OriginNotFoundError(Exception):
    pass


class SaveNotFoundError(Exception):
    pass


def build_starting_game_state(origin: Origin, character_name: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "turn_number": 0,
        "player": {
            "name": character_name,
            "origin_id": origin.id,
            "origin_label": origin.name,
            "location_id": origin.start_location_id,
            "traits": list(origin.starting_traits),
        },
        "inventory": [
            {"item_id": entry.item_id, "quantity": entry.quantity, "equipped": False}
            for entry in origin.starting_inventory
        ],
        "characters": {},
        "world_flags": {},
        "quests": [],
        "story_summary": "",
        "recent_context": [{"role": "narrator", "content": origin.opening_hook}],
    }


async def create_save(
    db: AsyncSession,
    content: GameContent,
    user_id: str,
    origin_id: str,
    slot_name: str | None,
    character_name: str | None,
) -> SaveSlot:
    origin = next((o for o in content.origins.origins if o.id == origin_id), None)
    if origin is None:
        raise OriginNotFoundError()

    game_state = build_starting_game_state(origin, character_name or "Traveler")

    save = SaveSlot(
        user_id=user_id,
        name=slot_name or origin.name,
        origin_id=origin.id,
        game_state_json=game_state,
        content_version=str(content.world.version),
    )
    db.add(save)
    await db.flush()

    db.add(
        StoryMessage(
            save_slot_id=save.id,
            role=MessageRole.NARRATOR,
            content=origin.opening_hook,
            turn_number=0,
        )
    )

    return save


async def list_saves(db: AsyncSession, user_id: str) -> list[SaveSlot]:
    result = await db.scalars(
        select(SaveSlot)
        .where(SaveSlot.user_id == user_id, SaveSlot.archived_at.is_(None))
        .order_by(SaveSlot.updated_at.desc())
    )
    return list(result)


async def get_owned_save(db: AsyncSession, user_id: str, save_id: str) -> SaveSlot:
    save = await db.get(SaveSlot, save_id)
    # Same not-found error for "doesn't exist" and "belongs to someone
    # else" - the API layer maps both to 404, not 403, so a save ID doesn't
    # leak whether it exists to a non-owner.
    if save is None or save.user_id != user_id:
        raise SaveNotFoundError()
    return save


async def get_save_messages(db: AsyncSession, save_id: str, limit: int = 20) -> list[StoryMessage]:
    result = await db.scalars(
        select(StoryMessage)
        .where(StoryMessage.save_slot_id == save_id)
        # A turn writes both a player and a narrator message under the same
        # turn_number (Task 33) - created_at breaks that tie so the player's
        # message always sorts before the narrator's reply to it.
        .order_by(StoryMessage.turn_number.desc(), StoryMessage.created_at.desc())
        .limit(limit)
    )
    return list(reversed(result.all()))


async def update_save(
    db: AsyncSession,
    user_id: str,
    save_id: str,
    name: str | None,
    archived: bool | None,
) -> SaveSlot:
    save = await get_owned_save(db, user_id, save_id)
    if name is not None:
        save.name = name
    if archived is True:
        save.archived_at = utcnow()
    elif archived is False:
        save.archived_at = None
    return save
