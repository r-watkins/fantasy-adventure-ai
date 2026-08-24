from collections.abc import AsyncIterator, Iterator
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


@pytest.fixture(autouse=True)
def _no_real_dotenv_in_tests(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # A developer's own backend/.env (e.g. for the Task 47 Gemini canary
    # test) must never leak into the test suite - found live: with a real
    # .env setting LLM_PROVIDER=gemini, every test constructing Settings(...)
    # directly (not through get_settings()) silently picked that up instead
    # of the code-level "mock" default, since pydantic-settings reads
    # env_file at each Settings() instantiation regardless of which fields
    # the caller explicitly passes. Tests must be hermetic to local dev
    # environment files - patch env_file off globally for the whole suite.
    # get_settings() is also process-wide lru_cache'd, so clear it too - a
    # previous test may have already cached a Settings() built from the
    # real .env before this fixture's patch took effect.
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


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
