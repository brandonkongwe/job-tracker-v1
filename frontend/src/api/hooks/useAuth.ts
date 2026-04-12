import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "@/stores/authStore"

const BASE = import.meta.env.VITE_API_URL ?? ""

async function post(path: string, body: unknown, token?: string) {
  const res = await fetch(`${BASE}${path}`, {
    method:  "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })
  return res
}

// Login
export function useLogin() {
  const navigate    = useNavigate()
  const setAuth     = useAuthStore((s) => s.setAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const res = await post("/api/v1/auth/login/", credentials)
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? "Invalid email or password")
      }
      return res.json()
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access, data.refresh)
      queryClient.clear()
      navigate("/dashboard")
    },
  })
}

// Register
export function useRegister() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async (payload: {
      email: string
      first_name: string
      last_name: string
      password: string
      password_confirm: string
    }) => {
      const res = await post("/api/v1/auth/register/", payload)
      if (!res.ok) { const e = await res.json(); throw e }
      return res.json()
    },
    onSuccess: () => navigate("/login?registered=true"),
  })
}

// Logout
export function useLogout() {
  const navigate     = useNavigate()
  const logout       = useAuthStore((s) => s.logout)
  const refreshToken = useAuthStore((s) => s.refreshToken)
  const accessToken  = useAuthStore((s) => s.accessToken)
  const queryClient  = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await post("/api/v1/auth/logout/", { refresh: refreshToken }, accessToken ?? undefined)
      }
    },
    onSettled: () => {
      logout()
      queryClient.clear()
      navigate("/login")
    },
  })
}