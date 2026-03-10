import { apiClient } from './client'
import type { BookDetail, BookListResponse, CatalogFilters } from '@/types/catalog'
import type { RefItem } from '@/types/admin'

export async function fetchGenres(): Promise<RefItem[]> {
  const { data } = await apiClient.get<RefItem[]>('/catalog/genres')
  return data ?? []
}

export async function fetchAuthors(): Promise<RefItem[]> {
  const { data } = await apiClient.get<RefItem[]>('/catalog/authors')
  return data ?? []
}

export async function fetchAgeRatings(): Promise<RefItem[]> {
  const { data } = await apiClient.get<RefItem[]>('/catalog/age-ratings')
  return data ?? []
}

export async function fetchLanguages(): Promise<RefItem[]> {
  const { data } = await apiClient.get<RefItem[]>('/catalog/languages')
  return data ?? []
}

export async function fetchTags(): Promise<RefItem[]> {
  const { data } = await apiClient.get<RefItem[]>('/catalog/tags')
  return data ?? []
}

export async function fetchBooks(filters: CatalogFilters = {}): Promise<BookListResponse> {
  const params = new URLSearchParams()
  if (filters.page != null) params.set('page', String(filters.page))
  if (filters.size != null) params.set('size', String(filters.size))
  if (filters.search) params.set('search', filters.search)
  if (filters.genre) params.set('genre', filters.genre)
  if (filters.age_rating) params.set('age_rating', filters.age_rating)
  if (filters.language) params.set('language', filters.language)
  if (filters.available_only) params.set('available_only', 'true')
  const { data } = await apiClient.get<BookListResponse>(
    `/catalog/books?${params.toString()}`
  )
  return data
}

export async function fetchBook(id: number): Promise<BookDetail> {
  const { data } = await apiClient.get<BookDetail>(`/catalog/books/${id}`)
  return data
}
