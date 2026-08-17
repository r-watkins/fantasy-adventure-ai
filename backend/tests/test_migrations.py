import sqlite3
from pathlib import Path

from alembic.config import Config

from alembic import command
from app.core.config import get_settings

EXPECTED_TABLES = {
    "users",
    "sessions",
    "save_slots",
    "story_messages",
    "user_settings",
    "alembic_version",
}


def _alembic_config(database_url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_alembic_upgrade_head_creates_all_tables(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "migration_check.db"
    database_url = f"sqlite+aiosqlite:///{db_path}"
    config = _alembic_config(database_url)

    # env.py resolves its target database via get_settings().database_url,
    # not the Config object passed in here - Settings is @lru_cache'd, and an
    # earlier test in this same process may have already cached the default
    # DATABASE_URL. Force a fresh read for the duration of this test only.
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    try:
        # alembic's command API drives its own event loop (via env.py's
        # asyncio.run()), so this must stay a plain sync test - calling it
        # from inside an already-running async test would raise.
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in rows}

    assert EXPECTED_TABLES <= tables
