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

export interface Item {
  id: string
  name: string
  category: string
  rarity: string
  description: string
  tags: string[]
  usable_in_prompt: boolean
}

export function listItems(): Promise<Item[]> {
  return apiClient.get<Item[]>('/api/content/items')
}

export interface Location {
  id: string
  name: string
  description: string
}

export function listLocations(): Promise<Location[]> {
  return apiClient.get<Location[]>('/api/content/locations')
}
