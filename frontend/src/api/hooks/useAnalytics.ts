import { useQuery } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/authStore"

const STALE = 1000 * 60 * 5

async function analyticsGet(path: string, params?: Record<string, string | number>) {
  const token   = useAuthStore.getState().accessToken
  const baseUrl = import.meta.env.VITE_API_URL ?? ""
  const url     = new URL(`${baseUrl}${path}`, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)))
  }
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function useDashboard() {
  return useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn:  () => analyticsGet("/api/v1/analytics/dashboard/"),
    staleTime: STALE,
  })
}

export function useWeeklyVolume(weeks = 12) {
  return useQuery({
    queryKey: ["analytics", "weekly-volume", weeks],
    queryFn:  () => analyticsGet("/api/v1/analytics/volume/weekly/", { weeks }),
    staleTime: STALE,
  })
}

export function useMonthlyVolume(months = 12) {
  return useQuery({
    queryKey: ["analytics", "monthly-volume", months],
    queryFn:  () => analyticsGet("/api/v1/analytics/volume/monthly/", { months }),
    staleTime: STALE,
  })
}

export function useConversionFunnel() {
  return useQuery({
    queryKey: ["analytics", "funnel"],
    queryFn:  () => analyticsGet("/api/v1/analytics/funnel/"),
    staleTime: STALE,
  })
}

export function useStageDuration() {
  return useQuery({
    queryKey: ["analytics", "stage-duration"],
    queryFn:  () => analyticsGet("/api/v1/analytics/stage-duration/"),
    staleTime: STALE,
  })
}

export function useResponseRate() {
  return useQuery({
    queryKey: ["analytics", "response-rate"],
    queryFn:  () => analyticsGet("/api/v1/analytics/response-rate/"),
    staleTime: STALE,
  })
}

export function useActivityHeatmap() {
  return useQuery({
    queryKey: ["analytics", "heatmap"],
    queryFn:  () => analyticsGet("/api/v1/analytics/heatmap/"),
    staleTime: STALE,
  })
}