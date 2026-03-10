import { apiClient } from './client'
import type {
  ReservationCreateResponse,
  ReservationListResponse,
} from '@/types/reservation'

export async function createReservation(bookId: number): Promise<ReservationCreateResponse> {
  const { data } = await apiClient.post<ReservationCreateResponse>(
    '/reservations',
    { book_id: bookId }
  )
  return data
}

export async function fetchMyReservations(): Promise<ReservationListResponse> {
  const { data } = await apiClient.get<ReservationListResponse>('/reservations')
  return data
}

export async function cancelReservation(reservationId: number): Promise<void> {
  await apiClient.patch(`/reservations/${reservationId}/cancel`)
}
