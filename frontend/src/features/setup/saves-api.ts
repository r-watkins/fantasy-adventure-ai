import { apiClient } from '@/lib/api-client'

export interface SaveSlotSummary {
  id: string
  name: string
  origin_id: string
  created_at: string
  updated_at: string
  archived_at: string | null
}

export function listSaves(): Promise<SaveSlotSummary[]> {
  return apiClient.get<SaveSlotSummary[]>('/api/saves')
}

export function archiveSave(saveId: string): Promise<SaveSlotSummary> {
  return apiClient.patch<SaveSlotSummary>(`/api/saves/${saveId}`, { archived: true })
}

export interface CreateSaveParams {
  originId: string
  characterName?: string
}

export function createSave({ originId, characterName }: CreateSaveParams): Promise<SaveSlotSummary> {
  return apiClient.post<SaveSlotSummary>('/api/saves', {
    origin_id: originId,
    character_name: characterName,
  })
}

export interface StoryMessage {
  role: 'player' | 'narrator' | 'system'
  content: string
  turn_number: number
  created_at: string
}

export interface InventoryEntry {
  item_id: string
  quantity: number
  equipped: boolean
}

export interface Quest {
  quest_id: string
  status: 'active' | 'completed' | 'failed'
  objective: string
}

// Grows field-by-field as later frontend tasks need more of the documented
// game_state_json shape (world_flags, characters, etc - see the backend's
// app/game/game_state.py for the full schema).
export interface GameStatePreview {
  player: {
    name: string
    location_id: string
  }
  inventory: InventoryEntry[]
  quests: Quest[]
}

export interface SaveSlotDetail extends SaveSlotSummary {
  game_state_json: GameStatePreview
  messages: StoryMessage[]
}

export function getSave(saveId: string): Promise<SaveSlotDetail> {
  return apiClient.get<SaveSlotDetail>(`/api/saves/${saveId}`)
}
