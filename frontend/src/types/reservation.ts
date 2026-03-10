export interface ReservationItem {
  id: number
  book_id: number
  book_title: string
  book_author: string
  book_cover_url?: string | null
  book_copy_id: number
  status: string
  delivery_date: string
  due_return_date: string
  delivery_address: string
  delivery_status: string
  created_at: string
  issued_at: string | null
  returned_at: string | null
  is_overdue: boolean
}

export interface ReservationListResponse {
  items: ReservationItem[]
  total: number
}

export interface ReservationCreateResponse {
  delivery_id: number
  delivery_date: string
  due_return_date: string
  address: string
  reservation_ids: number[]
  message: string
}
