from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_content, get_current_user
from app.db.session import get_db_session
from app.game.content_schemas import GameContent
from app.models.user import User
from app.schemas.saves import (
    CreateSaveRequest,
    SaveSlotDetail,
    SaveSlotSummary,
    UpdateSaveRequest,
)
from app.services.save_service import (
    OriginNotFoundError,
    SaveNotFoundError,
    create_save,
    get_owned_save,
    get_save_messages,
    list_saves,
    update_save,
)

router = APIRouter(prefix="/saves", tags=["saves"])


@router.post("", response_model=SaveSlotSummary, status_code=status.HTTP_201_CREATED)
async def create_save_slot(
    body: CreateSaveRequest,
    user: User = Depends(get_current_user),
    content: GameContent = Depends(get_content),
    db: AsyncSession = Depends(get_db_session),
) -> SaveSlotSummary:
    try:
        save = await create_save(
            db, content, user.id, body.origin_id, body.slot_name, body.character_name
        )
    except OriginNotFoundError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown origin_id"
        ) from exc

    return SaveSlotSummary.model_validate(save)


@router.get("", response_model=list[SaveSlotSummary])
async def list_save_slots(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[SaveSlotSummary]:
    saves = await list_saves(db, user.id)
    return [SaveSlotSummary.model_validate(save) for save in saves]


@router.get("/{save_id}", response_model=SaveSlotDetail)
async def get_save_slot(
    save_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SaveSlotDetail:
    try:
        save = await get_owned_save(db, user.id, save_id)
    except SaveNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Save not found") from exc

    messages = await get_save_messages(db, save.id)

    return SaveSlotDetail(
        id=save.id,
        name=save.name,
        origin_id=save.origin_id,
        created_at=save.created_at,
        updated_at=save.updated_at,
        archived_at=save.archived_at,
        game_state_json=save.game_state_json,
        messages=messages,
    )


@router.patch("/{save_id}", response_model=SaveSlotSummary)
async def patch_save_slot(
    save_id: str,
    body: UpdateSaveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SaveSlotSummary:
    try:
        save = await update_save(db, user.id, save_id, body.name, body.archived)
    except SaveNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Save not found") from exc

    return SaveSlotSummary.model_validate(save)
