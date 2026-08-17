from pathlib import Path

import pytest

from app.game.content_loader import ContentValidationError, load_content

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"

VALID_WORLD = """
world_id: test_realm
version: 1
name: Test Realm
tone: Testing tone.
core_lore: []
locations:
  - id: loc_a
    name: Location A
    description: A place.
"""

VALID_ITEMS = """
items:
  - id: item_a
    name: Item A
    category: tool
    rarity: common
    description: A thing.
"""

VALID_NPCS = "npcs: []\n"

VALID_ORIGINS = """
origins:
  - id: origin_a
    name: Origin A
    tagline: A start.
    description: A beginning.
    start_location_id: loc_a
    starting_inventory:
      - item_id: item_a
        quantity: 1
    opening_hook: Something happens.
"""

VALID_NARRATOR_PROMPT = "Be a good narrator.\n"


def _write_content_dir(tmp_path: Path, **overrides: str) -> Path:
    content_dir = tmp_path / "content"
    (content_dir / "prompts").mkdir(parents=True)

    files = {
        "world.yaml": VALID_WORLD,
        "items.yaml": VALID_ITEMS,
        "npcs.yaml": VALID_NPCS,
        "starting_origins.yaml": VALID_ORIGINS,
        "prompts/narrator_system.md": VALID_NARRATOR_PROMPT,
    }
    files.update(overrides)

    for relative_path, text in files.items():
        (content_dir / relative_path).write_text(text, encoding="utf-8")

    return content_dir


def test_load_content_against_real_repo_content() -> None:
    content = load_content(REPO_CONTENT_DIR)

    assert {"tavern_cook", "wheat_farmer"} <= content.origin_ids
    assert content.narrator_system_prompt.strip() != ""

    for origin in content.origins.origins:
        assert origin.start_location_id in content.location_ids
        for entry in origin.starting_inventory:
            assert entry.item_id in content.item_ids


def test_load_content_succeeds_on_valid_minimal_content(tmp_path: Path) -> None:
    content_dir = _write_content_dir(tmp_path)

    content = load_content(content_dir)

    assert content.origin_ids == {"origin_a"}
    assert content.item_ids == {"item_a"}
    assert content.location_ids == {"loc_a"}


def test_missing_content_file_raises(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()

    with pytest.raises(ContentValidationError, match="Missing content file"):
        load_content(content_dir)


def test_duplicate_item_id_raises(tmp_path: Path) -> None:
    duplicate_items = """
items:
  - id: item_a
    name: Item A
    category: tool
    rarity: common
    description: A thing.
  - id: item_a
    name: Item A Again
    category: tool
    rarity: common
    description: Another thing with the same id.
"""
    content_dir = _write_content_dir(tmp_path, **{"items.yaml": duplicate_items})

    with pytest.raises(ContentValidationError, match="Duplicate item id"):
        load_content(content_dir)


def test_origin_with_unknown_start_location_raises(tmp_path: Path) -> None:
    bad_origins = """
origins:
  - id: origin_a
    name: Origin A
    tagline: A start.
    description: A beginning.
    start_location_id: does_not_exist
    starting_inventory: []
    opening_hook: Something happens.
"""
    content_dir = _write_content_dir(tmp_path, **{"starting_origins.yaml": bad_origins})

    with pytest.raises(ContentValidationError, match="unknown start_location_id"):
        load_content(content_dir)


def test_origin_with_unknown_starting_item_raises(tmp_path: Path) -> None:
    bad_origins = """
origins:
  - id: origin_a
    name: Origin A
    tagline: A start.
    description: A beginning.
    start_location_id: loc_a
    starting_inventory:
      - item_id: does_not_exist
        quantity: 1
    opening_hook: Something happens.
"""
    content_dir = _write_content_dir(tmp_path, **{"starting_origins.yaml": bad_origins})

    with pytest.raises(ContentValidationError, match="unknown item_id"):
        load_content(content_dir)


def test_schema_violation_raises(tmp_path: Path) -> None:
    # Missing required fields (name, category, rarity, description) on the item.
    invalid_items = "items:\n  - id: item_a\n"
    content_dir = _write_content_dir(tmp_path, **{"items.yaml": invalid_items})

    with pytest.raises(ContentValidationError, match="Content schema validation failed"):
        load_content(content_dir)
