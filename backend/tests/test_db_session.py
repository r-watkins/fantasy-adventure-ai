import pytest
from asgi_lifespan import LifespanManager
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import create_engine, create_session_factory, get_db_session
from app.main import create_app

pytestmark = pytest.mark.anyio


async def test_engine_applies_sqlite_pragmas(tmp_path) -> None:
    db_path = tmp_path / "pragma_check.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_path}")

    async with engine.connect() as conn:
        journal_mode = (await conn.execute(text("PRAGMA journal_mode"))).scalar()
        foreign_keys = (await conn.execute(text("PRAGMA foreign_keys"))).scalar()
        synchronous = (await conn.execute(text("PRAGMA synchronous"))).scalar()

    assert journal_mode == "wal"
    assert foreign_keys == 1
    assert synchronous == 1  # NORMAL

    await engine.dispose()


async def test_session_factory_has_expire_on_commit_disabled() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        assert session.sync_session.expire_on_commit is False

    await engine.dispose()


async def test_get_db_session_dependency_is_wired_through_lifespan(tmp_path) -> None:
    db_path = tmp_path / "dependency_check.db"
    app = create_app()
    app.state.settings = Settings(database_url=f"sqlite+aiosqlite:///{db_path}")

    async def select_one(session: AsyncSession = Depends(get_db_session)) -> dict[str, int]:
        result = await session.execute(text("SELECT 1"))
        return {"value": result.scalar_one()}

    app.add_api_route("/api/_test/select-one", select_one, methods=["GET"])

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/_test/select-one")

    assert response.status_code == 200
    assert response.json() == {"value": 1}
