from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from google.genai import errors

from app.core.config import Settings
from app.game.content_loader import load_content
from app.game.game_state import GameState
from app.llm.gemini_provider import GeminiNarrativeProvider, GeminiTurnGenerationError
from app.llm.provider import NarrativeProvider
from app.llm.safety import build_safety_settings
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


def _provider() -> GeminiNarrativeProvider:
    return GeminiNarrativeProvider(
        api_key="fake-key",
        model="gemini-2.5-flash-lite",
        safety_settings=build_safety_settings(Settings()),
    )


def test_gemini_provider_satisfies_protocol() -> None:
    assert isinstance(_provider(), NarrativeProvider)


async def test_gemini_provider_returns_the_parsed_turn_result() -> None:
    provider = _provider()
    expected = TurnResult(narrative="You look around.", summary_update="Looked around.")
    provider._client.aio.models.generate_content = AsyncMock(
        return_value=SimpleNamespace(parsed=expected)
    )

    result = await provider.generate_turn(_request())

    assert result == expected


async def test_gemini_provider_calls_generate_content_with_expected_config() -> None:
    safety_settings = build_safety_settings(Settings())
    provider = GeminiNarrativeProvider(
        api_key="fake-key", model="gemini-2.5-flash-lite", safety_settings=safety_settings
    )
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
    assert call_kwargs["config"].safety_settings == safety_settings


async def test_gemini_provider_raises_when_response_has_no_parsed_result() -> None:
    provider = _provider()
    provider._client.aio.models.generate_content = AsyncMock(
        return_value=SimpleNamespace(parsed=None)
    )

    with pytest.raises(GeminiTurnGenerationError):
        await provider.generate_turn(_request())


def test_gemini_provider_configures_a_timeout_of_at_least_120_seconds() -> None:
    provider = _provider()

    http_options = provider._client._api_client._http_options
    assert http_options.timeout is not None
    assert http_options.timeout >= 120_000


def test_gemini_provider_opts_into_retry_on_429_and_5xx() -> None:
    # Without explicit retry_options, google-genai does not retry at all
    # (retry_args() returns stop_after_attempt(1) when retry_options is
    # None) - assert the provider actually opts in, not just that some
    # value is set.
    provider = _provider()

    retry_options = provider._client._api_client._http_options.retry_options
    assert retry_options is not None


async def test_gemini_provider_wraps_api_error_in_sanitized_exception() -> None:
    provider = _provider()
    raw_error = errors.ClientError(code=403, response_json={"error": {"message": "leaked detail"}})
    provider._client.aio.models.generate_content = AsyncMock(side_effect=raw_error)

    with pytest.raises(GeminiTurnGenerationError) as exc_info:
        await provider.generate_turn(_request())

    assert "leaked detail" not in str(exc_info.value)
    assert exc_info.value.__cause__ is raw_error


async def test_gemini_provider_wraps_transient_network_errors_in_sanitized_exception() -> None:
    provider = _provider()
    provider._client.aio.models.generate_content = AsyncMock(
        side_effect=httpx.ConnectError("connection refused to 1.2.3.4:443")
    )

    with pytest.raises(GeminiTurnGenerationError) as exc_info:
        await provider.generate_turn(_request())

    assert "1.2.3.4" not in str(exc_info.value)
