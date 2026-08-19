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
}

export function listOrigins(): Promise<Origin[]> {
  return apiClient.get<Origin[]>('/api/content/origins')
}
