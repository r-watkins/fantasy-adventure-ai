"""Endpoint-level coverage for Task 44's error-handling requirement: a
narrative-generation failure (Gemini API error, timeout, or an
unparsable response) must surface as a sanitized 502 to the client - never
raw provider text - with zero state mutation, matching
test_turns_action_rejection.py's pattern for proposed-action rejection.
"""

from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_narrative_provider
from app.core.config import Settings
from app.llm.gemini_provider import GeminiTurnGenerationError
from app.llm.schemas import NarrativeTurnRequest, TurnResult
from app.main import create_app

pytestmark = pytest.mark.anyio

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


def _provider_raising(message: str):
    class _FailingProvider:
        async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult:
            raise GeminiTurnGenerationError(message)

    return _FailingProvider()


async def test_turn_endpoint_surfaces_sanitized_502_with_zero_mutation(
    migrated_db_url: str,
) -> None:
    secret_looking_message = "Gemini API request failed (status 403 PERMISSION_DENIED)"
    provider = _provider_raising(secret_looking_message)

    app = create_app()
    app.state.settings = Settings(database_url=migrated_db_url, content_dir=str(REPO_CONTENT_DIR))
    app.dependency_overrides[get_narrative_provider] = lambda: provider

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            register_response = await client.post(
                "/api/auth/register",
                json={"email": "gemini-failure@example.com", "password": "correct horse battery"},
            )
            assert register_response.status_code == 201

            create_response = await client.post(
                "/api/saves", json={"origin_id": "tavern_cook", "character_name": "Avery"}
            )
            assert create_response.status_code == 201
            save_id = create_response.json()["id"]

            before = await client.get(f"/api/saves/{save_id}")
            before_body = before.json()

            response = await client.post(
                f"/api/saves/{save_id}/turns", json={"message": "I try something risky."}
            )

            assert response.status_code == 502
            body = response.json()
            assert body["detail"] == (
                "The narrator's response could not be processed. Please try again."
            )
            # The raw exception message (which could echo provider status
            # text) must never leak into the client-facing response.
            assert secret_looking_message not in str(body)

            after = await client.get(f"/api/saves/{save_id}")
            after_body = after.json()

            assert after_body["game_state_json"] == before_body["game_state_json"]
            assert after_body["messages"] == before_body["messages"]
