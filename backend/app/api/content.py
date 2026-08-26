from fastapi import APIRouter, Depends

from app.api.deps import get_content, get_current_user
from app.game.content_schemas import Faction, GameContent, Item, Location, Npc, Origin
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


@router.get("/locations", response_model=list[Location])
async def list_locations(
    content: GameContent = Depends(get_content),
    _user: User = Depends(get_current_user),
) -> list[Location]:
    return content.world.locations


@router.get("/npcs", response_model=list[Npc])
async def list_npcs(
    content: GameContent = Depends(get_content),
    _user: User = Depends(get_current_user),
) -> list[Npc]:
    return content.npcs.npcs


@router.get("/factions", response_model=list[Faction])
async def list_factions(
    content: GameContent = Depends(get_content),
    _user: User = Depends(get_current_user),
) -> list[Faction]:
    return content.factions.factions
