import { apiClient } from '@/lib/api-client'

export interface OriginStartingItem {
  item_id: string
  quantity: number
}

export interface Origin {
  id: string
  name: string
  tagline: string
  description: string
  start_location_id: string
  starting_traits: string[]
  starting_inventory: OriginStartingItem[]
  opening_hook: string
  playstyle?: string | null
  start_npc_ids?: string[]
  special_capabilities?: string[]
  opening_quest_id?: string | null
}

export function listOrigins(): Promise<Origin[]> {
  return apiClient.get<Origin[]>('/api/content/origins')
}

export interface Item {
  id: string
  name: string
  category: string
  rarity: string
  description: string
  tags: string[]
  usable_in_prompt: boolean
  effects?: string[]
}

export function listItems(): Promise<Item[]> {
  return apiClient.get<Item[]>('/api/content/items')
}

export interface SubLocation {
  id: string
  name: string
}

export interface Location {
  id: string
  name: string
  description: string
  region_id?: string | null
  type?: string | null
  mood?: string | null
  sublocations?: SubLocation[]
  npc_ids?: string[]
  available_actions?: string[]
  secrets?: string[]
  discoverable_items?: string[]
  quest_hooks?: string[]
}

export function listLocations(): Promise<Location[]> {
  return apiClient.get<Location[]>('/api/content/locations')
}

export interface Npc {
  id: string
  name: string
  role: string
  description: string
  motivations: string[]
  secrets: string[]
  title?: string | null
  faction_id?: string | null
  location_id?: string | null
  voice?: string | null
  personality_traits?: string[]
  fears?: string | null
  relationship_hooks?: string[]
  humor_hook?: string | null
  quest_ids?: string[]
}

export function listNpcs(): Promise<Npc[]> {
  return apiClient.get<Npc[]>('/api/content/npcs')
}

export interface FactionReputationEffects {
  positive: string
  negative: string
}

export interface Faction {
  id: string
  name: string
  motto: string
  public_role: string
  leader: string
  values: string[]
  methods: string[]
  reputation_effects: FactionReputationEffects
}

export function listFactions(): Promise<Faction[]> {
  return apiClient.get<Faction[]>('/api/content/factions')
}
