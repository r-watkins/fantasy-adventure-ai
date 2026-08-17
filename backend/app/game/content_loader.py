from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.game.content_schemas import (
    GameContent,
    Item,
    ItemsContent,
    Location,
    Npc,
    NpcsContent,
    Origin,
    OriginsContent,
    WorldContent,
)


class ContentValidationError(RuntimeError):
    """Raised when repository content fails schema or cross-reference validation.

    Intentionally lets startup crash loudly rather than run with broken
    content - content is treated as untrusted input at load time.
    """


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        raise ContentValidationError(f"Missing content file: {path}")
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def _read_text(path: Path) -> str:
    if not path.exists():
        raise ContentValidationError(f"Missing content file: {path}")
    return path.read_text(encoding="utf-8")


def _require_unique_ids(
    entries: list[Location] | list[Item] | list[Npc] | list[Origin], label: str
) -> None:
    seen: set[str] = set()
    for entry in entries:
        if entry.id in seen:
            raise ContentValidationError(f"Duplicate {label} id: {entry.id!r}")
        seen.add(entry.id)


def load_content(content_dir: Path) -> GameContent:
    try:
        world = WorldContent.model_validate(_read_yaml(content_dir / "world.yaml"))
        items = ItemsContent.model_validate(_read_yaml(content_dir / "items.yaml"))
        npcs = NpcsContent.model_validate(_read_yaml(content_dir / "npcs.yaml"))
        origins = OriginsContent.model_validate(
            _read_yaml(content_dir / "starting_origins.yaml")
        )
    except ValidationError as exc:
        raise ContentValidationError(f"Content schema validation failed: {exc}") from exc

    narrator_system_prompt = _read_text(content_dir / "prompts" / "narrator_system.md")

    _require_unique_ids(world.locations, "location")
    _require_unique_ids(items.items, "item")
    _require_unique_ids(npcs.npcs, "npc")
    _require_unique_ids(origins.origins, "origin")

    location_ids = {location.id for location in world.locations}
    item_ids = {item.id for item in items.items}

    for origin in origins.origins:
        if origin.start_location_id not in location_ids:
            raise ContentValidationError(
                f"Origin {origin.id!r} references unknown "
                f"start_location_id {origin.start_location_id!r}"
            )
        for entry in origin.starting_inventory:
            if entry.item_id not in item_ids:
                raise ContentValidationError(
                    f"Origin {origin.id!r} references unknown "
                    f"item_id {entry.item_id!r} in starting_inventory"
                )

    return GameContent(
        world=world,
        items=items,
        npcs=npcs,
        origins=origins,
        narrator_system_prompt=narrator_system_prompt,
    )
