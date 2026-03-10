export interface BookListEntry {
  id: number
  author: string
  title: string
  cover_url: string | null
  genre: string | null
  age_rating: string
  language: string
  tags: string[] | null
  available_count: number
  total_count: number
}

export interface BookDetail extends BookListEntry {
  description: string | null
  /** Дата возврата (YYYY-MM-DD), если книга на руках. */
  earliest_return_date: string | null
  /** Число человек в очереди (когда книга на руках). */
  queue_count: number
  /** Текущий пользователь держит эту книгу. */
  current_user_has_book: boolean
  /** Место в очереди (1-based) или null. */
  queue_position: number | null
  /** Всего в очереди. */
  queue_total: number
}

export interface BookListResponse {
  items: BookListEntry[]
  total: number
  page: number
  size: number
  pages: number
}

export interface CatalogFilters {
  page?: number
  size?: number
  search?: string
  genre?: string
  age_rating?: string
  language?: string
  available_only?: boolean
}
