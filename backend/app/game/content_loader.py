from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.game.content_schemas import (
    EncounterPoolsContent,
    Ending,
    EndingsContent,
    Faction,
    FactionsContent,
    GameContent,
    Item,
    ItemsContent,
    Location,
    Npc,
    NpcsContent,
    Origin,
    OriginsContent,
    QuestsContent,
    QuestTemplate,
    Region,
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


_IdentifiedEntry = Location | Region | Item | Npc | Origin | Faction | QuestTemplate | Ending


def _require_unique_ids(entries: list[_IdentifiedEntry], label: str) -> None:
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
        factions = FactionsContent.model_validate(_read_yaml(content_dir / "factions.yaml"))
        quests = QuestsContent.model_validate(_read_yaml(content_dir / "quests.yaml"))
        endings = EndingsContent.model_validate(_read_yaml(content_dir / "endings.yaml"))
        encounters = EncounterPoolsContent.model_validate(
            _read_yaml(content_dir / "encounters.yaml")
        )
    except ValidationError as exc:
        raise ContentValidationError(f"Content schema validation failed: {exc}") from exc

    narrator_system_prompt = _read_text(content_dir / "prompts" / "narrator_system.md")

    _require_unique_ids(world.regions, "region")
    _require_unique_ids(world.locations, "location")
    _require_unique_ids(items.items, "item")
    _require_unique_ids(npcs.npcs, "npc")
    _require_unique_ids(origins.origins, "origin")
    _require_unique_ids(factions.factions, "faction")
    _require_unique_ids(quests.quests, "quest")
    _require_unique_ids(endings.endings, "ending")

    region_ids = {region.id for region in world.regions}
    location_ids = {location.id for location in world.locations}
    item_ids = {item.id for item in items.items}
    faction_ids = {faction.id for faction in factions.factions}
    quest_ids = {quest.id for quest in quests.quests}

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
        if origin.opening_quest_id is not None and origin.opening_quest_id not in quest_ids:
            raise ContentValidationError(
                f"Origin {origin.id!r} references unknown "
                f"opening_quest_id {origin.opening_quest_id!r}"
            )

    for location in world.locations:
        if location.region_id is not None and location.region_id not in region_ids:
            raise ContentValidationError(
                f"Location {location.id!r} references unknown region_id {location.region_id!r}"
            )
        for item_id in location.discoverable_items:
            if item_id not in item_ids:
                raise ContentValidationError(
                    f"Location {location.id!r} references unknown "
                    f"discoverable_items entry {item_id!r}"
                )
        for quest_id in location.quest_hooks:
            if quest_id not in quest_ids:
                raise ContentValidationError(
                    f"Location {location.id!r} references unknown quest_hooks entry {quest_id!r}"
                )

    for npc in npcs.npcs:
        if npc.faction_id is not None and npc.faction_id not in faction_ids:
            raise ContentValidationError(
                f"NPC {npc.id!r} references unknown faction_id {npc.faction_id!r}"
            )
        if npc.location_id is not None and npc.location_id not in location_ids:
            raise ContentValidationError(
                f"NPC {npc.id!r} references unknown location_id {npc.location_id!r}"
            )
        for quest_id in npc.quest_ids:
            if quest_id not in quest_ids:
                raise ContentValidationError(
                    f"NPC {npc.id!r} references unknown quest_ids entry {quest_id!r}"
                )

    return GameContent(
        world=world,
        items=items,
        npcs=npcs,
        origins=origins,
        factions=factions,
        quests=quests,
        endings=endings,
        encounters=encounters,
        narrator_system_prompt=narrator_system_prompt,
    )
