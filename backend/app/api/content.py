from fastapi import APIRouter, Depends

from app.api.deps import get_content, get_current_user
from app.game.content_schemas import GameContent, Item, Origin
from app.models.user import User

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/origins", response_model=list[Origin])
async def list_origins(
    content: GameContent = Depends(get_content),
    _user: User = Depends(get_current_user),
) -> list[Origin]:
    return content.origins.origins


@router.get("/items", response_model=list[Item])
async def list_items(
    content: GameContent = Depends(get_content),
    _user: User = Depends(get_current_user),
) -> list[Item]:
    return content.items.items
