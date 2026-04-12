/**
 * Typed API client built on openapi-fetch.
 * Automatically attaches JWT access tokens to every request.
 * On 401, attempts one silent token refresh then retries.
 * On refresh failure, clears auth state and redirects to /login (i hope).
 */

import createClient, { type Middleware } from "openapi-fetch"
import type { paths } from "./schema"
import { useAuthStore } from "@/stores/authStore"

const BASE_URL = import.meta.env.VITE_API_URL ?? ""

export const apiClient = createClient<paths>({ baseUrl: BASE_URL })

// Middleware: attach Bearer token
const authMiddleware: Middleware = {
  async onRequest({ request }) {
    const token = useAuthStore.getState().accessToken
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`)
    }
    return request
  },

  async onResponse({ response, request }) {
    if (response.status !== 401) return response

    // Attempt silent refresh
    const refreshToken = useAuthStore.getState().refreshToken
    if (!refreshToken) {
      useAuthStore.getState().logout()
      return response
    }

    try {
      const refreshResponse = await fetch(`${BASE_URL}/api/v1/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: refreshToken }),
      })

      if (!refreshResponse.ok) throw new Error("Refresh failed")

      const { access } = await refreshResponse.json()
      useAuthStore.getState().setAccessToken(access)

      // Retry the original request with the new token
      request.headers.set("Authorization", `Bearer ${access}`)
      return fetch(request)
    } catch {
      useAuthStore.getState().logout()
      window.location.href = "/login"
      return response
    }
  },
}

apiClient.use(authMiddleware)