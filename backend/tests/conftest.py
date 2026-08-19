from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic.config import Config
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from alembic import command
from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.main import create_app

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    # `limiter` is a process-wide singleton (imported once, shared by every
    # app instance create_app() builds), so its in-memory counters would
    # otherwise leak across tests/test files that all hit the same
    # rate-limited endpoints from the same apparent client IP.
    limiter.reset()


def _alembic_config(database_url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


@pytest.fixture
def migrated_db_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    db_path = tmp_path / "test.db"
    database_url = f"sqlite+aiosqlite:///{db_path}"
    config = _alembic_config(database_url)

    # See test_migrations.py: alembic's command API drives its own event
    # loop, so this must run as plain sync fixture setup, not from inside an
    # already-running async test/fixture.
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    try:
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()

    return database_url


@pytest.fixture
async def client(migrated_db_url: str) -> AsyncIterator[AsyncClient]:
    app = create_app()
    app.state.settings = Settings(
        database_url=migrated_db_url,
        content_dir=str(REPO_CONTENT_DIR),
    )

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
