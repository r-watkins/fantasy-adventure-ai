"""Task 46: regression coverage proving no prompt text, session tokens,
provider API keys, or passwords ever reach the application's logs.

An audit of the full backend found only two logger call sites in the whole
codebase (both in app/api/turns.py, added by Tasks 33/44) - no SQL echo, no
print statements, no request/response body logging, and no logging anywhere
in the auth flow (app/api/auth.py never logs, so a password submitted at
/api/auth/login or /register can never reach a log record). This file locks
that in with caplog-based tests: it asserts app.state.narrative_provider's
own real error path (a Gemini API error carrying a distinctive fake key and
"leaked" response detail) never ends up in captured log output, and that a
distinctive player message and session token likewise never appear.
"""

import logging
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from google.genai import errors
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_narrative_provider
from app.core.config import Settings
from app.llm.gemini_provider import GeminiNarrativeProvider
from app.llm.safety import build_safety_settings
from app.main import create_app

pytestmark = pytest.mark.anyio

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"

_FAKE_API_KEY = "AIzaSy-FAKE-SECRET-KEY-000111"
_LEAKED_PROVIDER_DETAIL = "leaked-provider-response-detail-xyz"
_DISTINCTIVE_PLAYER_MESSAGE = "the-quick-brown-fox-player-message-marker"


def _failing_gemini_provider() -> GeminiNarrativeProvider:
    provider = GeminiNarrativeProvider(
        api_key=_FAKE_API_KEY,
        model="gemini-2.5-flash-lite",
        safety_settings=build_safety_settings(Settings()),
    )

    async def _raise(*args: object, **kwargs: object) -> None:
        raise errors.ClientError(
            code=403, response_json={"error": {"message": _LEAKED_PROVIDER_DETAIL}}
        )

    provider._client.aio.models.generate_content = _raise
    return provider


async def test_gemini_api_key_and_raw_provider_detail_never_reach_logs(
    migrated_db_url: str, caplog: pytest.LogCaptureFixture
) -> None:
    app = create_app()
    app.state.settings = Settings(database_url=migrated_db_url, content_dir=str(REPO_CONTENT_DIR))
    app.dependency_overrides[get_narrative_provider] = _failing_gemini_provider

    caplog.set_level(logging.DEBUG)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/register",
                json={"email": "log-audit@example.com", "password": "correct horse battery"},
            )
            create_response = await client.post(
                "/api/saves", json={"origin_id": "tavern_cook", "character_name": "Avery"}
            )
            save_id = create_response.json()["id"]

            response = await client.post(
                f"/api/saves/{save_id}/turns",
                json={"message": _DISTINCTIVE_PLAYER_MESSAGE},
            )
            assert response.status_code == 502

    assert _FAKE_API_KEY not in caplog.text
    assert _LEAKED_PROVIDER_DETAIL not in caplog.text
    assert _DISTINCTIVE_PLAYER_MESSAGE not in caplog.text


async def test_password_never_reaches_logs_across_register_login_logout(
    migrated_db_url: str, caplog: pytest.LogCaptureFixture
) -> None:
    app = create_app()
    app.state.settings = Settings(database_url=migrated_db_url, content_dir=str(REPO_CONTENT_DIR))
    password = "a-very-distinctive-passphrase-99"

    caplog.set_level(logging.DEBUG)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/register",
                json={"email": "password-audit@example.com", "password": password},
            )
            # A failed login attempt is exactly the path most likely to log
            # the submitted credential for debugging - assert it doesn't.
            await client.post(
                "/api/auth/login",
                json={"email": "password-audit@example.com", "password": "wrong-password"},
            )
            login_response = await client.post(
                "/api/auth/login",
                json={"email": "password-audit@example.com", "password": password},
            )
            session_cookie = login_response.cookies.get("session_token")
            await client.post("/api/auth/logout")

    assert password not in caplog.text
    assert "wrong-password" not in caplog.text
    if session_cookie:
        assert session_cookie not in caplog.text
