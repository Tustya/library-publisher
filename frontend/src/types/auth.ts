export interface User {
  id: number
  phone: string
  first_name: string | null
  last_name: string | null
  patronymic: string | null
  delivery_address: string | null
  is_active: boolean
  role: string
}

export interface UserUpdate {
  first_name?: string | null
  last_name?: string | null
  patronymic?: string | null
  phone?: string | null
  delivery_address?: string | null
}
