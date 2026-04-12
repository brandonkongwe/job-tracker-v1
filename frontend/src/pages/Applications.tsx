import { useState, useCallback } from "react"
import { Briefcase, Loader2, ChevronLeft, ChevronRight, Inbox } from "lucide-react"
import { useApplications } from "@/api/hooks/useApplications"
import { ApplicationCard } from "@/components/applications/ApplicationCard"
import { ApplicationFilters } from "@/components/applications/ApplicationFilters"
import { CreateApplicationDialog } from "@/components/applications/CreateApplicationDialog"
import { Button } from "@/components/ui/button"
import { useDebounce } from "@/lib/useDebounce"

export default function ApplicationsPage() {
  const [page, setPage]         = useState(1)
  const [search, setSearch]     = useState("")
  const [statuses, setStatuses] = useState<string[]>([])
  const [isActive, setIsActive] = useState<boolean | undefined>(undefined)
  const [ordering, setOrdering] = useState("-created_at")

  const debouncedSearch = useDebounce(search, 300)

  const { data, isPending, isError } = useApplications({
    page,
    page_size: 15,
    search:    debouncedSearch || undefined,
    status:    statuses.length > 0 ? statuses : undefined,
    is_active: isActive,
    ordering,
  })

  const handleStatusToggle = useCallback((s: string) => {
    setPage(1)
    setStatuses((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    )
  }, [])

  const handleSearch = useCallback((v: string) => {
    setSearch(v)
    setPage(1)
  }, [])

  const handleActiveToggle = useCallback(() => {
    setPage(1)
    setIsActive((prev) => (prev === true ? undefined : true))
  }, [])

  const handleReset = useCallback(() => {
    setSearch("")
    setStatuses([])
    setIsActive(undefined)
    setOrdering("-created_at")
    setPage(1)
  }, [])

  const pagination   = data?.pagination as any
  const applications = data?.results as any[] ?? []
  const totalPages   = pagination?.total_pages ?? 1
  const totalCount   = pagination?.count ?? 0

  return (
    <div className="flex flex-col gap-6 p-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Briefcase size={20} className="text-ink-muted" />
            <h1 className="font-display text-2xl text-ink">Applications</h1>
          </div>
          <p className="mt-0.5 text-sm text-ink-muted">
            {totalCount > 0
              ? `${totalCount} application${totalCount !== 1 ? "s" : ""} tracked`
              : "No applications yet"}
          </p>
        </div>
        <CreateApplicationDialog />
      </div>

      {/* Filters */}
      <ApplicationFilters
        search={search}
        statuses={statuses}
        isActive={isActive}
        ordering={ordering}
        onSearch={handleSearch}
        onStatusToggle={handleStatusToggle}
        onActiveToggle={handleActiveToggle}
        onOrderingChange={(v) => { setOrdering(v); setPage(1) }}
        onReset={handleReset}
      />

      {/* List */}
      {isPending ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={24} className="animate-spin text-ink-faint" />
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          Failed to load applications. Please refresh the page.
        </div>
      ) : applications.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border py-20 text-center">
          <Inbox size={36} className="text-ink-faint" />
          <div>
            <p className="font-medium text-ink">No applications found</p>
            <p className="text-sm text-ink-muted">
              {search || statuses.length > 0
                ? "Try adjusting your filters"
                : "Add your first application to get started"}
            </p>
          </div>
        </div>
      ) : (
        <div className="animate-fade-in space-y-2">
          {applications.map((app, i) => (
            <div
              key={app.id}
              className="animate-slide-up"
              style={{ animationDelay: `${i * 30}ms`, animationFillMode: "forwards" }}
            >
              <ApplicationCard application={app} />
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-border pt-4">
          <p className="text-sm text-ink-muted">
            Page {pagination?.current_page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!pagination?.has_previous}
              onClick={() => setPage((p) => p - 1)}
              className="gap-1"
            >
              <ChevronLeft size={14} />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!pagination?.has_next}
              onClick={() => setPage((p) => p + 1)}
              className="gap-1"
            >
              Next
              <ChevronRight size={14} />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}