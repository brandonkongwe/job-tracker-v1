import { Search, SlidersHorizontal, X } from "lucide-react"
import { Input } from "@/components/ui/index"
import { Button } from "@/components/ui/button"
import { STATUS_CONFIG } from "@/lib/utils"
import { cn } from "@/lib/utils"

interface Props {
  search:    string
  statuses:  string[]
  isActive:  boolean | undefined
  ordering:  string
  onSearch:     (v: string) => void
  onStatusToggle: (s: string) => void
  onActiveToggle: () => void
  onOrderingChange: (v: string) => void
  onReset: () => void
}

const ORDERING_OPTIONS = [
  { value: "-created_at",  label: "Newest first" },
  { value: "created_at",   label: "Oldest first" },
  { value: "company_name", label: "Company A-Z" },
  { value: "applied_date", label: "Applied date" },
  { value: "status",       label: "Status" },
]

export function ApplicationFilters({
  search,
  statuses,
  isActive,
  ordering,
  onSearch,
  onStatusToggle,
  onActiveToggle,
  onOrderingChange,
  onReset,
}: Props) {
  const hasFilters = search || statuses.length > 0 || isActive !== undefined

  return (
    <div className="space-y-3">
      {/* Search + sort row */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
          />
          <Input
            placeholder="Search by company, role, location…"
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <select
          value={ordering}
          onChange={(e) => onOrderingChange(e.target.value)}
          className="rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {ORDERING_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={onReset} className="gap-1.5 text-ink-muted">
            <X size={14} />
            Reset
          </Button>
        )}
      </div>

      {/* Status pills */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="flex items-center gap-1.5 text-xs text-ink-faint">
          <SlidersHorizontal size={12} />
          Filter
        </span>

        {/* Active toggle */}
        <button
          onClick={onActiveToggle}
          className={cn(
            "rounded-full border px-3 py-1 text-xs font-medium transition-all",
            isActive === true
              ? "border-ink bg-ink text-cream-DEFAULT"
              : "border-border text-ink-muted hover:border-ink/30 hover:text-ink"
          )}
        >
          Active only
        </button>

        {/* Status buttons */}
        {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
          <button
            key={key}
            onClick={() => onStatusToggle(key)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-all",
              statuses.includes(key)
                ? `${cfg.bg} ${cfg.text} border-transparent`
                : "border-border text-ink-muted hover:border-ink/30 hover:text-ink"
            )}
          >
            {cfg.label}
          </button>
        ))}
      </div>
    </div>
  )
}