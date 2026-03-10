/**
 * Запросы к эндпоинтам auth.
 */
import { apiClient, setStoredToken } from './client'
import type { User, UserUpdate } from '../types/auth'

export interface RegisterPayload {
  phone: string
  password: string
}

export interface LoginPayload {
  phone: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export async function register(phone: string, password: string): Promise<User> {
  const { data } = await apiClient.post<User>('/auth/register', { phone, password })
  return data
}

export async function login(phone: string, password: string): Promise<TokenResponse> {
  const form = new URLSearchParams()
  form.append('username', phone)
  form.append('password', password)
  const { data } = await apiClient.post<TokenResponse>('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  setStoredToken(data.access_token)
  return data
}

export async function fetchMe(): Promise<User> {
  const { data } = await apiClient.get<User>('/auth/me')
  return data
}

export async function updateProfile(payload: UserUpdate): Promise<User> {
  const { data } = await apiClient.patch<User>('/auth/me', payload)
  return data
}

export function logout(): void {
  setStoredToken(null)
}
