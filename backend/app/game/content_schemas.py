from pydantic import BaseModel


class Location(BaseModel):
    id: str
    name: str
    description: str


class WorldContent(BaseModel):
    world_id: str
    version: int
    name: str
    tone: str
    core_lore: list[str] = []
    locations: list[Location] = []


class Item(BaseModel):
    id: str
    name: str
    category: str
    rarity: str
    description: str
    tags: list[str] = []
    usable_in_prompt: bool = True


class ItemsContent(BaseModel):
    items: list[Item] = []


class Npc(BaseModel):
    id: str
    name: str
    role: str
    description: str
    motivations: list[str] = []
    secrets: list[str] = []


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


class OriginsContent(BaseModel):
    origins: list[Origin] = []


class GameContent(BaseModel):
    world: WorldContent
    items: ItemsContent
    npcs: NpcsContent
    origins: OriginsContent
    narrator_system_prompt: str

    @property
    def location_ids(self) -> set[str]:
        return {location.id for location in self.world.locations}

    @property
    def item_ids(self) -> set[str]:
        return {item.id for item in self.items.items}

    @property
    def npc_ids(self) -> set[str]:
        return {npc.id for npc in self.npcs.npcs}

    @property
    def origin_ids(self) -> set[str]:
        return {origin.id for origin in self.origins.origins}
