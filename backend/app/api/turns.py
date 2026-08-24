import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_content, get_current_user, get_narrative_provider
from app.core.rate_limit import limiter
from app.db.session import get_db_session
from app.game.content_schemas import GameContent
from app.llm.gemini_provider import GeminiTurnGenerationError
from app.llm.provider import NarrativeProvider
from app.models.user import User
from app.schemas.turns import SubmitTurnRequest, TurnResponse
from app.services.action_validation_service import ActionValidationError
from app.services.save_service import SaveNotFoundError
from app.services.turn_service import submit_turn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/saves", tags=["turns"])


@router.post("/{save_id}/turns", response_model=TurnResponse)
@limiter.limit("20/minute")
async def submit_turn_endpoint(
    request: Request,
    save_id: str,
    body: SubmitTurnRequest,
    user: User = Depends(get_current_user),
    content: GameContent = Depends(get_content),
    provider: NarrativeProvider = Depends(get_narrative_provider),
    db: AsyncSession = Depends(get_db_session),
) -> TurnResponse:
    try:
        player_message, narrator_message, new_state = await submit_turn(
            db, content, provider, user.id, save_id, body.message
        )
    except SaveNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Save not found") from exc
    except ActionValidationError as exc:
        # Sanitized diagnostic only - never the raw provider response to the
        # client (source doc §7). exc.message is our own validator's
        # description of what was wrong (e.g. "Unknown item_id 'x'"), not
        # provider text, so it's safe to log verbatim.
        logger.warning("Turn action validation failed for save %s: %s", save_id, exc.message)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="The narrator's response could not be processed. Please try again.",
        ) from exc
    except GeminiTurnGenerationError as exc:
        # str(exc) is always our own sanitized, generic description (see
        # GeminiTurnGenerationError's docstring) - never the raw provider
        # response, so it's safe to log verbatim. Zero state mutation:
        # submit_turn raises this before any db.add/save mutation happens.
        logger.warning("Turn narrative generation failed for save %s: %s", save_id, exc)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="The narrator's response could not be processed. Please try again.",
        ) from exc

    return TurnResponse(
        player_message=player_message,
        narrator_message=narrator_message,
        game_state=new_state.model_dump(mode="json"),
        turn_number=new_state.turn_number,
    )
