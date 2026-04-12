/**
 * Global auth store via Zustand.
 * Persists tokens to localStorage so the session survives page refresh.
 * Access token is short-lived (60 min) — the API client handles silent refresh.
 */

import { create } from "zustand"
import { persist } from "zustand/middleware"

interface User {
  id: string
  email: string
  full_name: string
  role: "job_seeker" | "admin"
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null

  // Actions
  setAuth: (user: User, accessToken: string, refreshToken: string) => void
  setAccessToken: (token: string) => void
  logout: () => void
  isAuthenticated: () => boolean
  isAdmin: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setAuth: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken }),

      setAccessToken: (accessToken) => set({ accessToken }),

      logout: () => set({ user: null, accessToken: null, refreshToken: null }),

      isAuthenticated: () => !!get().accessToken && !!get().user,

      isAdmin: () => get().user?.role === "admin",
    }),
    {
      name: "job-tracker-auth",
      // Only persist tokens + user — nothing else
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
)