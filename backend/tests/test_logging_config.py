"""Regression test for a real gap found while auditing Task 46: with the
root logger at DEBUG (e.g. a developer debugging locally, or a verbose
LOG_LEVEL in production), aiosqlite logs every SQL statement with its bound
parameters - which includes story_messages.content (a player's free-form
turn message and the narrator's reply, verbatim) as an INSERT parameter.
Confirmed by hand before this fix existed: registering a user and creating
a save, with caplog.set_level(logging.DEBUG), produced aiosqlite log
records containing the literal SQL parameter tuples for sessions.token_hash
and users.password_hash lookups. create_app() now pins aiosqlite (and
SQLAlchemy's own dormant engine/pool loggers) to WARNING regardless of the
root level - this test proves that holds even when a caller cranks root
logging all the way up, and that a real player message written through a
full register -> save -> turn flow never appears in DEBUG-level log output.
"""

import logging
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app

pytestmark = pytest.mark.anyio

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"

_DISTINCTIVE_PLAYER_MESSAGE = "the-quick-brown-fox-jumps-over-the-lazy-dog-marker"


async def test_aiosqlite_query_logging_stays_suppressed_even_at_root_debug_level(
    migrated_db_url: str, caplog: pytest.LogCaptureFixture
) -> None:
    app = create_app()
    app.state.settings = Settings(database_url=migrated_db_url, content_dir=str(REPO_CONTENT_DIR))

    caplog.set_level(logging.DEBUG)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/register",
                json={"email": "sql-log-audit@example.com", "password": "correct horse battery"},
            )
            create_response = await client.post(
                "/api/saves", json={"origin_id": "tavern_cook", "character_name": "Avery"}
            )
            save_id = create_response.json()["id"]
            response = await client.post(
                f"/api/saves/{save_id}/turns",
                json={"message": _DISTINCTIVE_PLAYER_MESSAGE},
            )
            assert response.status_code == 200

    aiosqlite_records = [r for r in caplog.records if r.name.startswith("aiosqlite")]
    assert aiosqlite_records == []
    assert _DISTINCTIVE_PLAYER_MESSAGE not in caplog.text
    assert "correct horse battery" not in caplog.text
