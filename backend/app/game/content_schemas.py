from typing import Any

from pydantic import BaseModel


class SubLocation(BaseModel):
    id: str
    name: str


class Location(BaseModel):
    id: str
    name: str
    description: str
    region_id: str | None = None
    type: str | None = None
    mood: str | None = None
    sublocations: list[SubLocation] = []
    npc_ids: list[str] = []
    available_actions: list[str] = []
    secrets: list[str] = []
    discoverable_items: list[str] = []
    quest_hooks: list[str] = []


class Region(BaseModel):
    id: str
    name: str
    description: str
    threats: list[str] = []


class WorldContent(BaseModel):
    world_id: str
    version: int
    name: str
    tone: str
    core_lore: list[str] = []
    regions: list[Region] = []
    locations: list[Location] = []


class Item(BaseModel):
    id: str
    name: str
    category: str
    rarity: str
    description: str
    tags: list[str] = []
    usable_in_prompt: bool = True
    effects: list[str] = []


class ItemsContent(BaseModel):
    items: list[Item] = []


class Npc(BaseModel):
    id: str
    name: str
    role: str
    description: str
    motivations: list[str] = []
    secrets: list[str] = []
    title: str | None = None
    faction_id: str | None = None
    location_id: str | None = None
    voice: str | None = None
    personality_traits: list[str] = []
    fears: str | None = None
    relationship_hooks: list[str] = []
    humor_hook: str | None = None
    quest_ids: list[str] = []


class NpcsContent(BaseModel):
    npcs: list[Npc] = []


class StartingInventoryEntry(BaseModel):
    item_id: str
    quantity: int = 1


class Origin(BaseModel):
    id: str
    name: str
    tagline: str
    description: str
    start_location_id: str
    starting_traits: list[str] = []
    starting_inventory: list[StartingInventoryEntry] = []
    opening_hook: str
    playstyle: str | None = None
    start_npc_ids: list[str] = []
    special_capabilities: list[str] = []
    opening_quest_id: str | None = None


class OriginsContent(BaseModel):
    origins: list[Origin] = []


class FactionReputationEffects(BaseModel):
    positive: str
    negative: str


class Faction(BaseModel):
    id: str
    name: str
    motto: str
    public_role: str
    leader: str
    values: list[str] = []
    methods: list[str] = []
    reputation_effects: FactionReputationEffects


class FactionsContent(BaseModel):
    factions: list[Faction] = []


class QuestStage(BaseModel):
    id: str
    objective: str


class QuestTemplate(BaseModel):
    id: str
    title: str
    type: str
    summary: str
    stages: list[QuestStage] = []
    entry_sources: list[str] = []
    key_npcs: list[str] = []
    rewards: list[str] = []
    branching_outcomes: list[str] = []
    initial_status: str = "locked"
    unlock_conditions: dict[str, Any] | None = None
    primary_endings: list[str] = []


class QuestsContent(BaseModel):
    quests: list[QuestTemplate] = []


class Ending(BaseModel):
    id: str
    name: str
    premise: str
    required_evidence: list[str] = []
    typical_allies: list[str] = []
    benefits: str
    costs: str
    epilogue_variants: list[str] = []


class EndingsContent(BaseModel):
    endings: list[Ending] = []


class EncounterPoolsContent(BaseModel):
    encounter_pools: dict[str, list[str]] = {}


class GameContent(BaseModel):
    world: WorldContent
    items: ItemsContent
    npcs: NpcsContent
    origins: OriginsContent
    factions: FactionsContent
    quests: QuestsContent
    endings: EndingsContent
    encounters: EncounterPoolsContent
    narrator_system_prompt: str

    @property
    def location_ids(self) -> set[str]:
        return {location.id for location in self.world.locations}

    @property
    def region_ids(self) -> set[str]:
        return {region.id for region in self.world.regions}

    @property
    def item_ids(self) -> set[str]:
        return {item.id for item in self.items.items}

    @property
    def npc_ids(self) -> set[str]:
        return {npc.id for npc in self.npcs.npcs}

    @property
    def origin_ids(self) -> set[str]:
        return {origin.id for origin in self.origins.origins}

    @property
    def faction_ids(self) -> set[str]:
        return {faction.id for faction in self.factions.factions}

    @property
    def quest_template_ids(self) -> set[str]:
        return {quest.id for quest in self.quests.quests}
