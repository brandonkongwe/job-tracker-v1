import { Link } from "react-router-dom"
import {
  Building2,
  MapPin,
  Calendar,
  ExternalLink,
  FileText,
  Wifi,
  WifiOff,
  MonitorSmartphone,
} from "lucide-react"
import { StatusBadge } from "./StatusBadge"
import { formatDate, WORK_MODE_LABELS } from "@/lib/utils"

interface Props {
  application: {
    id: string
    company_name: string
    job_title: string
    location?: string
    work_mode?: string
    status: string
    salary_range?: string
    source?: string
    applied_date?: string
    document_count?: number
    created_at: string
  }
}

const WORK_MODE_ICONS: Record<string, React.ReactNode> = {
  remote:  <Wifi size={11} />,
  hybrid:  <MonitorSmartphone size={11} />,
  on_site: <WifiOff size={11} />,
}

export function ApplicationCard({ application: app }: Props) {
  return (
    <Link
      to={`/applications/${app.id}`}
      className="group flex items-center gap-4 rounded-lg border border-border bg-card px-5 py-4 transition-all hover:border-ink/20 hover:shadow-sm"
    >
      {/* Company initial */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-cream-darker text-sm font-semibold text-ink-soft">
        {app.company_name.charAt(0)}
      </div>

      {/* Main info */}
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate font-medium text-ink">{app.job_title}</p>
            <p className="flex items-center gap-1.5 truncate text-sm text-ink-muted">
              <Building2 size={12} />
              {app.company_name}
            </p>
          </div>
          <StatusBadge status={app.status} className="shrink-0" />
        </div>

        {/* Meta row */}
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-faint">
          {app.location && (
            <span className="flex items-center gap-1">
              <MapPin size={11} />
              {app.location}
            </span>
          )}
          {app.work_mode && (
            <span className="flex items-center gap-1">
              {WORK_MODE_ICONS[app.work_mode]}
              {WORK_MODE_LABELS[app.work_mode] ?? app.work_mode}
            </span>
          )}
          {app.applied_date && (
            <span className="flex items-center gap-1">
              <Calendar size={11} />
              Applied {formatDate(app.applied_date)}
            </span>
          )}
          {(app.document_count ?? 0) > 0 && (
            <span className="flex items-center gap-1">
              <FileText size={11} />
              {app.document_count} doc{app.document_count !== 1 ? "s" : ""}
            </span>
          )}
          {app.salary_range && app.salary_range !== "Not disclosed" && (
            <span className="ml-auto font-medium text-ink-muted">
              {app.salary_range}
            </span>
          )}
        </div>
      </div>

      <ExternalLink
        size={14}
        className="shrink-0 text-ink-faint opacity-0 transition-opacity group-hover:opacity-100"
      />
    </Link>
  )
}