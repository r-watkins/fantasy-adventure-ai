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
