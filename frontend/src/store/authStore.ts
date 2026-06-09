import { create } from 'zustand'
import { api } from '@/lib/api'
import type { User } from '@/lib/types'

interface AuthState {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true })
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    const me = await api.get('/auth/me')
    set({ user: me.data, isLoading: false })
  },

  register: async (email, password, fullName) => {
    set({ isLoading: true })
    await api.post('/auth/register', { email, password, full_name: fullName })
    // Auto-login after register
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    const me = await api.get('/auth/me')
    set({ user: me.data, isLoading: false })
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null })
  },

  fetchMe: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    try {
      const { data } = await api.get('/auth/me')
      set({ user: data })
    } catch {
      // token expired — interceptor already clears it
    }
  },
}))
