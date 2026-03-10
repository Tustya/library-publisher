/**
 * Состояние авторизации: пользователь, вход, выход, проверка по токену.
 */
import { ref, computed } from 'vue'
import { getStoredToken } from '@/api/client'
import { fetchMe, login as apiLogin, logout as apiLogout } from '@/api/auth'
import type { User } from '@/types/auth'

const user = ref<User | null>(null)
const loading = ref(false)
const initialized = ref(false)

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function init(): Promise<void> {
    if (initialized.value) return
    const token = getStoredToken()
    if (!token) {
      initialized.value = true
      return
    }
    loading.value = true
    try {
      user.value = await fetchMe()
    } catch {
      user.value = null
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  async function login(phone: string, password: string): Promise<void> {
    await apiLogin(phone, password)
    await init()
    user.value = (await fetchMe()) as User
  }

  function logout(): void {
    apiLogout()
    user.value = null
  }

  function setUser(u: User | null): void {
    user.value = u
  }

  return {
    user,
    loading,
    initialized,
    isAuthenticated,
    isAdmin,
    init,
    login,
    logout,
    setUser,
  }
}
