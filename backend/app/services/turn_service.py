from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.game.content_schemas import GameContent
from app.game.game_state import ContextMessage, GameState
from app.llm.provider import NarrativeProvider
from app.llm.schemas import NarrativeTurnRequest
from app.models.enums import MessageRole
from app.models.story_message import StoryMessage
from app.services.action_validation_service import validate_and_apply_actions
from app.services.save_service import get_owned_save


async def submit_turn(
    db: AsyncSession,
    content: GameContent,
    provider: NarrativeProvider,
    user_id: str,
    save_id: str,
    player_message_text: str,
) -> tuple[StoryMessage, StoryMessage, GameState]:
    """Raises SaveNotFoundError (unowned/missing save) or
    ActionValidationError (the provider's proposed actions failed
    validation). Neither leaves any trace in the database or in the caller's
    save object - nothing is written until every action has been validated.
    """
    save = await get_owned_save(db, user_id, save_id)
    state = GameState.model_validate(save.game_state_json)

    request = NarrativeTurnRequest(
        game_state=state, content=content, player_message=player_message_text
    )
    result = await provider.generate_turn(request)

    new_state = validate_and_apply_actions(state, content, result.proposed_actions)

    new_turn_number = state.turn_number + 1
    new_state.turn_number = new_turn_number
    new_state.story_summary = result.summary_update

    window = get_settings().recent_context_window
    new_state.recent_context = [
        *state.recent_context,
        ContextMessage(role=MessageRole.PLAYER, content=player_message_text),
        ContextMessage(role=MessageRole.NARRATOR, content=result.narrative),
    ][-window:]

    player_row = StoryMessage(
        save_slot_id=save.id,
        role=MessageRole.PLAYER,
        content=player_message_text,
        turn_number=new_turn_number,
    )
    narrator_row = StoryMessage(
        save_slot_id=save.id,
        role=MessageRole.NARRATOR,
        content=result.narrative,
        turn_number=new_turn_number,
    )
    db.add(player_row)
    db.add(narrator_row)

    save.game_state_json = new_state.model_dump(mode="json")

    await db.flush()

    return player_row, narrator_row, new_state
