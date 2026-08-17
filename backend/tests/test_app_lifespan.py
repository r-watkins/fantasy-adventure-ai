from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager

from app.core.config import Settings
from app.main import create_app

pytestmark = pytest.mark.anyio

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


async def test_lifespan_populates_app_state_content(tmp_path: Path) -> None:
    db_path = tmp_path / "lifespan_content_check.db"
    app = create_app()
    app.state.settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_path}",
        content_dir=str(REPO_CONTENT_DIR),
    )

    async with LifespanManager(app):
        assert {"tavern_cook", "wheat_farmer"} <= app.state.content.origin_ids


async def test_lifespan_fails_fast_on_invalid_content_dir(tmp_path: Path) -> None:
    db_path = tmp_path / "lifespan_bad_content_check.db"
    empty_content_dir = tmp_path / "empty_content"
    empty_content_dir.mkdir()

    app = create_app()
    app.state.settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_path}",
        content_dir=str(empty_content_dir),
    )

    with pytest.raises(Exception, match="Missing content file"):
        async with LifespanManager(app):
            pass
