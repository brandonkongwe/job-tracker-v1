import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query"
import { useAuthStore } from "@/stores/authStore"

export interface ApplicationFilters {
  page?: number
  page_size?: number
  search?: string
  status?: string[]
  work_mode?: string[]
  is_active?: boolean
  applied_after?: string
  applied_before?: string
  ordering?: string
}

export interface PaginatedApplications {
  pagination: {
    count:        number
    total_pages:  number
    current_page: number
    page_size:    number
    has_next:     boolean
    has_previous: boolean
    next:         string | null
    previous:     string | null
  }
  results: any[]
}

// Shared fetch helper
// Uses the Vite proxy (/api → localhost:8000) in dev.
// In production VITE_API_URL is set to the real domain.
async function authFetch(path: string, init?: RequestInit): Promise<Response> {
  const token   = useAuthStore.getState().accessToken
  const baseUrl = import.meta.env.VITE_API_URL ?? ""
  return fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })
}

// List applications
export function useApplications(filters: ApplicationFilters = {}) {
  return useQuery({
    queryKey: ["applications", filters],
    queryFn: async (): Promise<PaginatedApplications> => {
      const params = new URLSearchParams()
      if (filters.page)      params.set("page",      String(filters.page))
      if (filters.page_size) params.set("page_size",  String(filters.page_size))
      if (filters.search)    params.set("search",     filters.search)
      if (filters.ordering)  params.set("ordering",   filters.ordering)
      if (filters.is_active !== undefined)
        params.set("is_active", String(filters.is_active))
      filters.status?.forEach((s) => params.append("status",    s))
      filters.work_mode?.forEach((w) => params.append("work_mode", w))
      if (filters.applied_after)  params.set("applied_after",  filters.applied_after)
      if (filters.applied_before) params.set("applied_before", filters.applied_before)

      const res = await authFetch(`/api/v1/applications/?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
    placeholderData: keepPreviousData,
  })
}

// Single application
export function useApplication(id: string | undefined) {
  return useQuery({
    queryKey: ["applications", id],
    queryFn: async () => {
      const res = await authFetch(`/api/v1/applications/${id}/`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
    enabled: !!id,
  })
}

// Create application
export function useCreateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const res = await authFetch("/api/v1/applications/", {
        method: "POST",
        body:   JSON.stringify(body),
      })
      if (!res.ok) { const e = await res.json(); throw e }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] })
      queryClient.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

// Update application
export function useUpdateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: Record<string, unknown> }) => {
      const res = await authFetch(`/api/v1/applications/${id}/`, {
        method: "PATCH",
        body:   JSON.stringify(body),
      })
      if (!res.ok) { const e = await res.json(); throw e }
      return res.json()
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["applications"] })
      queryClient.invalidateQueries({ queryKey: ["applications", id] })
      queryClient.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

// Delete application
export function useDeleteApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await authFetch(`/api/v1/applications/${id}/`, { method: "DELETE" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] })
      queryClient.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

// Upload document
export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      applicationId, file, documentType,
    }: { applicationId: string; file: File; documentType: string }) => {
      const token = useAuthStore.getState().accessToken
      const baseUrl = import.meta.env.VITE_API_URL ?? ""
      const formData = new FormData()
      formData.append("file", file)
      formData.append("document_type", documentType)
      // Note: do NOT set Content-Type header — browser sets it with boundary
      const res = await fetch(
        `${baseUrl}/api/v1/applications/${applicationId}/documents/`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData }
      )
      if (!res.ok) { const e = await res.json(); throw e }
      return res.json()
    },
    onSuccess: (_data, { applicationId }) => {
      queryClient.invalidateQueries({ queryKey: ["applications", applicationId] })
    },
  })
}

// Delete document
export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      applicationId, documentId,
    }: { applicationId: string; documentId: string }) => {
      const res = await authFetch(
        `/api/v1/applications/${applicationId}/documents/${documentId}/`,
        { method: "DELETE" }
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    },
    onSuccess: (_data, { applicationId }) => {
      queryClient.invalidateQueries({ queryKey: ["applications", applicationId] })
    },
  })
}

// Status history
export function useStatusHistory(applicationId: string | undefined) {
  return useQuery({
    queryKey: ["applications", applicationId, "history"],
    queryFn: async () => {
      const res = await authFetch(`/api/v1/applications/${applicationId}/history/`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json() as Promise<any[]>
    },
    enabled: !!applicationId,
  })
}