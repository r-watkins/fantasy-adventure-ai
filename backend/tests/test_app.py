import pytest

from app.main import create_app

pytestmark = pytest.mark.anyio


async def test_create_app_boots_with_settings() -> None:
    app = create_app()

    assert app.title == "Fantasy AI Adventure API"
    assert app.state.settings.llm_provider == "mock"
