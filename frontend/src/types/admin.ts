export interface BookCopyDetail {
  id: number
  book_id: number
  unique_number: string
  status: string
  cover_url: string | null
}

export interface BookDetailWithCopies {
  id: number
  author: string
  title: string
  description: string | null
  cover_url: string | null
  genre: string | null
  age_rating: string
  language: string
  tags: string[] | null
  author_ids: number[]
  genre_id: number | null
  age_rating_id: number
  language_id: number
  tag_ids: number[]
  copies: BookCopyDetail[]
}

export interface BookCreate {
  author_ids: number[]
  title: string
  description?: string | null
  cover_url?: string | null
  genre_id?: number | null
  age_rating_id: number
  language_id: number
  tag_ids?: number[] | null
}

export interface BookUpdate {
  author_ids?: number[]
  title?: string
  description?: string | null
  cover_url?: string | null
  genre_id?: number | null
  age_rating_id?: number
  language_id?: number
  tag_ids?: number[] | null
}

export interface RefItem {
  id: number
  name: string
}

export interface BookCopyCreate {
  unique_number: string
  status: string
  cover_url?: string | null
}

export interface BookCopyUpdate {
  unique_number?: string
  status?: string
  cover_url?: string | null
}

export interface AdminReservationItem {
  id: number
  delivery_id: number
  book_id: number
  book_title: string
  book_author: string
  book_cover_url: string | null
  book_copy_id: number
  book_copy_number: string
  user_id: number
  user_phone: string
  user_name: string | null
  delivery_address: string
  delivery_date: string
  due_return_date: string
  status: string
  delivery_status: string
  created_at: string
  issued_at: string | null
  returned_at: string | null
  is_overdue: boolean
}

export interface AdminOverdueItem {
  reservation_id: number
  user_id: number
  user_phone: string
  user_name: string | null
  book_id: number
  book_title: string
  book_author: string
  book_copy_number: string
  due_return_date: string
  days_overdue: number
}

export interface AdminReaderItem {
  id: number
  phone: string
  first_name: string | null
  last_name: string | null
  patronymic: string | null
  delivery_address: string | null
  is_active: boolean
  role: string
}
