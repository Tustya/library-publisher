import { apiClient } from './client'

export async function joinQueue(bookId: number): Promise<{ ok: boolean; message: string }> {
  const { data } = await apiClient.post<{ ok: boolean; message: string }>(
    `/queue/books/${bookId}`
  )
  return data
}

export async function leaveQueue(bookId: number): Promise<{ ok: boolean; message: string }> {
  const { data } = await apiClient.delete<{ ok: boolean; message: string }>(
    `/queue/books/${bookId}`
  )
  return data
}
