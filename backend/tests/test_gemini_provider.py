from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.game.content_loader import load_content
from app.game.game_state import GameState
from app.llm.gemini_provider import GeminiNarrativeProvider, GeminiTurnGenerationError
from app.llm.provider import NarrativeProvider
from app.llm.schemas import NarrativeTurnRequest, TurnResult
from app.services.save_service import build_starting_game_state

pytestmark = pytest.mark.anyio

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _request() -> NarrativeTurnRequest:
    content = load_content(REPO_CONTENT_DIR)
    origin = next(o for o in content.origins.origins if o.id == "tavern_cook")
    state = GameState.model_validate(build_starting_game_state(origin, "Avery"))
    return NarrativeTurnRequest(
        game_state=state, content=content, player_message="I look around the tavern."
    )


def test_gemini_provider_satisfies_protocol() -> None:
    provider = GeminiNarrativeProvider(api_key="fake-key", model="gemini-2.5-flash-lite")
    assert isinstance(provider, NarrativeProvider)


async def test_gemini_provider_returns_the_parsed_turn_result() -> None:
    provider = GeminiNarrativeProvider(api_key="fake-key", model="gemini-2.5-flash-lite")
    expected = TurnResult(narrative="You look around.", summary_update="Looked around.")
    provider._client.aio.models.generate_content = AsyncMock(
        return_value=SimpleNamespace(parsed=expected)
    )

    result = await provider.generate_turn(_request())

    assert result == expected


async def test_gemini_provider_calls_generate_content_with_expected_config() -> None:
    provider = GeminiNarrativeProvider(api_key="fake-key", model="gemini-2.5-flash-lite")
    generate_content = AsyncMock(
        return_value=SimpleNamespace(parsed=TurnResult(narrative="n", summary_update="s"))
    )
    provider._client.aio.models.generate_content = generate_content

    await provider.generate_turn(_request())

    generate_content.assert_awaited_once()
    call_kwargs = generate_content.await_args.kwargs
    assert call_kwargs["model"] == "gemini-2.5-flash-lite"
    assert "I look around the tavern." in call_kwargs["contents"]
    assert call_kwargs["config"].response_mime_type == "application/json"
    assert call_kwargs["config"].response_schema is TurnResult
    assert call_kwargs["config"].system_instruction == _request().content.narrator_system_prompt


async def test_gemini_provider_raises_when_response_has_no_parsed_result() -> None:
    provider = GeminiNarrativeProvider(api_key="fake-key", model="gemini-2.5-flash-lite")
    provider._client.aio.models.generate_content = AsyncMock(
        return_value=SimpleNamespace(parsed=None)
    )

    with pytest.raises(GeminiTurnGenerationError):
        await provider.generate_turn(_request())
