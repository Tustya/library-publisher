import { apiClient } from './client'
import type {
  AdminOverdueItem,
  AdminReaderItem,
  AdminReservationItem,
  BookCopyCreate,
  BookCopyDetail,
  BookCopyUpdate,
  BookCreate,
  BookDetailWithCopies,
  BookUpdate,
  RefItem,
} from '@/types/admin'

export async function fetchAdminBook(id: number): Promise<BookDetailWithCopies> {
  const { data } = await apiClient.get<BookDetailWithCopies>(`/admin/books/${id}`)
  return data
}

export async function createBook(payload: BookCreate): Promise<BookDetailWithCopies> {
  const { data } = await apiClient.post<BookDetailWithCopies>('/admin/books', payload)
  return data
}

export async function updateBook(
  id: number,
  payload: BookUpdate
): Promise<BookDetailWithCopies> {
  const { data } = await apiClient.patch<BookDetailWithCopies>(
    `/admin/books/${id}`,
    payload
  )
  return data
}

export async function deleteBook(id: number): Promise<void> {
  await apiClient.delete(`/admin/books/${id}`)
}

export async function createTag(name: string): Promise<RefItem> {
  const { data } = await apiClient.post<RefItem>('/admin/tags', { name: name.trim() })
  return data
}

export async function createCopy(
  bookId: number,
  payload: BookCopyCreate
): Promise<BookCopyDetail> {
  const { data } = await apiClient.post<BookCopyDetail>(
    `/admin/books/${bookId}/copies`,
    payload
  )
  return data
}

export async function updateCopy(
  copyId: number,
  payload: BookCopyUpdate
): Promise<BookCopyDetail> {
  const { data } = await apiClient.patch<BookCopyDetail>(
    `/admin/copies/${copyId}`,
    payload
  )
  return data
}

export async function deleteCopy(copyId: number): Promise<void> {
  await apiClient.delete(`/admin/copies/${copyId}`)
}

export async function fetchAdminReservations(): Promise<AdminReservationItem[]> {
  const { data } = await apiClient.get<AdminReservationItem[]>('/admin/reservations')
  return data
}

export async function confirmReservationIssue(
  reservationId: number
): Promise<void> {
  await apiClient.patch(`/admin/reservations/${reservationId}/issue`)
}

export async function confirmReservationReturn(
  reservationId: number
): Promise<void> {
  await apiClient.patch(`/admin/reservations/${reservationId}/return`)
}

export async function fetchOverdue(): Promise<AdminOverdueItem[]> {
  const { data } = await apiClient.get<AdminOverdueItem[]>('/admin/overdue')
  return data
}

export async function fetchReaders(): Promise<AdminReaderItem[]> {
  const { data } = await apiClient.get<AdminReaderItem[]>('/admin/readers')
  return data
}
