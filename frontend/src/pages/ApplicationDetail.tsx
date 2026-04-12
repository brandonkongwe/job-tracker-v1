import { useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import {
  ArrowLeft, Building2, MapPin, Calendar, Globe, Briefcase,
  FileText, Upload, Trash2, Loader2, Clock, ChevronRight,
  ExternalLink, Bell, Edit2, Check,
} from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import {
  useApplication, useUpdateApplication, useDeleteApplication,
  useUploadDocument, useDeleteDocument, useStatusHistory,
} from "@/api/hooks/useApplications"
import { Button } from "@/components/ui/button"
import { Input, Label, Textarea } from "@/components/ui/index"
import {
  formatDate, formatDateTime, timeAgo,
  STATUS_CONFIG, WORK_MODE_LABELS, SOURCE_LABELS, cn,
} from "@/lib/utils"

const PIPELINE = ["saved","applied","screening","interview","offer","accepted"] as const

// Pipeline stepper
function PipelineStepper({ current, onSelect }: { current: string; onSelect: (s: string) => void }) {
  const currentIdx = PIPELINE.indexOf(current as typeof PIPELINE[number])
  return (
    <div className="flex items-center gap-0 overflow-x-auto pb-1">
      {PIPELINE.map((stage, i) => {
        const cfg     = STATUS_CONFIG[stage]
        const isActive = stage === current
        const isPast   = i < currentIdx
        return (
          <div key={stage} className="flex items-center">
            <button
              onClick={() => onSelect(stage)}
              className={cn(
                "flex flex-col items-center gap-1 px-3 py-2 text-xs font-medium transition-all rounded-md",
                isActive && `${cfg.bg} ${cfg.text}`,
                isPast   && "text-ink-faint",
                !isActive && !isPast && "text-ink-muted hover:text-ink"
              )}
            >
              <span className={cn(
                "flex h-6 w-6 items-center justify-center rounded-full border text-[10px]",
                isActive && `${cfg.bg} ${cfg.text} border-transparent`,
                isPast   && "border-ink-faint text-ink-faint",
                !isActive && !isPast && "border-border"
              )}>
                {isPast ? <Check size={10} /> : i + 1}
              </span>
              {cfg.label}
            </button>
            {i < PIPELINE.length - 1 && (
              <ChevronRight size={12} className={i < currentIdx ? "text-ink-faint" : "text-border"} />
            )}
          </div>
        )
      })}
      <div className="ml-3 flex items-center gap-1.5 border-l border-border pl-3">
        {["rejected","withdrawn"].map((s) => (
          <button key={s} onClick={() => onSelect(s)}
            className={cn(
              "rounded-full px-2.5 py-1 text-xs transition-all",
              current === s
                ? `${STATUS_CONFIG[s].bg} ${STATUS_CONFIG[s].text} font-medium`
                : "border border-border text-ink-faint hover:text-ink"
            )}
          >
            {STATUS_CONFIG[s].label}
          </button>
        ))}
      </div>
    </div>
  )
}

// Document row
function DocumentRow({ doc, applicationId }: { doc: any; applicationId: string }) {
  const deleteDoc = useDeleteDocument()
  const [confirming, setConfirming] = useState(false)
  return (
    <div className="flex items-center gap-3 rounded-md border border-border px-4 py-3">
      <FileText size={15} className="shrink-0 text-ink-faint" />
      <div className="min-w-0 flex-1">
        <a href={doc.file_url} target="_blank" rel="noreferrer"
          className="truncate text-sm font-medium text-ink hover:underline flex items-center gap-1">
          {doc.original_filename} <ExternalLink size={11} className="text-ink-faint" />
        </a>
        <p className="text-xs text-ink-faint">
          {doc.document_type === "cv" ? "CV / Resume" :
           doc.document_type === "cover_letter" ? "Cover Letter" : "Document"}
          {" · "}{doc.file_size_display} · Uploaded {timeAgo(doc.uploaded_at)}
        </p>
      </div>
      {confirming ? (
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-ink-muted">Delete?</span>
          <button onClick={() => { deleteDoc.mutate({ applicationId, documentId: doc.id }); setConfirming(false) }}
            className="rounded bg-red-50 px-2 py-1 text-xs text-red-600 hover:bg-red-100">Yes</button>
          <button onClick={() => setConfirming(false)} className="text-xs text-ink-faint hover:text-ink">No</button>
        </div>
      ) : (
        <button onClick={() => setConfirming(true)} className="rounded p-1 text-ink-faint hover:text-red-500">
          <Trash2 size={14} />
        </button>
      )}
    </div>
  )
}

// Upload zone
function UploadZone({ applicationId }: { applicationId: string }) {
  const upload = useUploadDocument()
  const [dragOver, setDragOver] = useState(false)
  const handleFile = (file: File) => upload.mutate({ applicationId, file, documentType: "cv" })
  return (
    <label className={cn(
      "flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed px-6 py-7 text-center transition-all",
      dragOver ? "border-ink bg-cream-darker" : "border-border hover:border-ink/30 hover:bg-cream-darker/50"
    )}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}
    >
      <input type="file" accept=".pdf,.doc,.docx" className="sr-only"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
      {upload.isPending
        ? <Loader2 size={20} className="animate-spin text-ink-faint" />
        : <Upload size={20} className="text-ink-faint" />}
      <div>
        <p className="text-sm font-medium text-ink">{upload.isPending ? "Uploading…" : "Drop or click to upload"}</p>
        <p className="text-xs text-ink-faint">PDF, DOC, DOCX · max 5 MB</p>
      </div>
    </label>
  )
}

// History timeline
function StatusTimeline({ applicationId }: { applicationId: string }) {
  const { data: history = [], isPending } = useStatusHistory(applicationId)
  if (isPending) return <p className="py-4 text-center text-sm text-ink-faint">Loading…</p>
  if (!history.length) return <p className="py-4 text-center text-sm text-ink-faint">No history yet.</p>
  return (
    <div>
      {[...history].reverse().map((entry: any, i: number) => (
        <div key={entry.id} className="flex gap-3">
          <div className="flex flex-col items-center">
            <div className={cn("mt-1 h-2.5 w-2.5 shrink-0 rounded-full border-2",
              i === 0 ? "border-ink bg-ink" : "border-border bg-cream-DEFAULT")} />
            {i < history.length - 1 && <div className="w-px flex-1 bg-border" />}
          </div>
          <div className="pb-4">
            <p className="text-sm font-medium text-ink">
              {entry.from_status
                ? `${entry.from_status_display} → ${entry.to_status_display}`
                : `Created as ${entry.to_status_display}`}
            </p>
            <p className="text-xs text-ink-faint">
              {formatDateTime(entry.changed_at)}
              {entry.note ? ` · ${entry.note}` : ""}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

// Edit schema
// salary fields are kept as plain strings in the form (avoid z.preprocess which
// makes TypeScript infer 'unknown' and breaks the resolver type). Coercion to
// number happens manually in onSubmit before the API call.
const editSchema = z.object({
  company_name:    z.string().min(1),
  job_title:       z.string().min(1),
  job_url:         z.string().url().or(z.literal("")).optional(),
  location:        z.string().optional(),
  work_mode:       z.string().optional(),
  applied_date:    z.string().optional(),
  salary_min:      z.string().optional(),
  salary_max:      z.string().optional(),
  salary_currency: z.string().optional(),
  source:          z.string().optional(),
  notes:           z.string().optional(),
})
type EditData = z.infer<typeof editSchema>

// Main component
export default function ApplicationDetailPage() {
  const { id }   = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)

  const { data: app, isPending, isError } = useApplication(id)
  const updateApp = useUpdateApplication()
  const deleteApp = useDeleteApplication()

  const { register, handleSubmit, reset } = useForm<EditData>({
    resolver: zodResolver(editSchema),
    values: app ? {
      company_name: app.company_name, job_title: app.job_title,
      job_url: (app as any).job_url ?? "", location: app.location ?? "",
      work_mode: app.work_mode ?? "", applied_date: (app.applied_date as any) ?? "",
      salary_min: (app as any).salary_min?.toString() ?? "", salary_max: (app as any).salary_max?.toString() ?? "",
      salary_currency: (app as any).salary_currency ?? "BWP",
      source: app.source ?? "", notes: (app as any).notes ?? "",
    } : undefined,
  })

  if (isPending) return (
    <div className="flex h-full items-center justify-center py-32">
      <Loader2 size={24} className="animate-spin text-ink-faint" />
    </div>
  )
  if (isError || !app) return (
    <div className="p-8">
      <p className="text-sm text-red-600">Application not found. <Link to="/applications" className="underline">Go back</Link></p>
    </div>
  )

  const documents = (app as any).documents ?? []

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-8 animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-ink-muted">
        <Link to="/applications" className="flex items-center gap-1 hover:text-ink">
          <ArrowLeft size={14} /> Applications
        </Link>
        <ChevronRight size={12} className="text-border" />
        <span className="text-ink">{app.job_title}</span>
      </div>

      {/* Header card */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-cream-darker text-xl font-bold text-ink-soft">
              {app.company_name.charAt(0)}
            </div>
            <div>
              <h1 className="font-display text-2xl text-ink">{app.job_title}</h1>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-ink-muted">
                <span className="flex items-center gap-1"><Building2 size={13} />{app.company_name}</span>
                {app.location && <span className="flex items-center gap-1"><MapPin size={13} />{app.location}</span>}
                {app.work_mode && <span>{WORK_MODE_LABELS[app.work_mode] ?? app.work_mode}</span>}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link to="/reminders" state={{ prefillApplicationId: id }}
              className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs text-ink-muted hover:border-ink/20 hover:text-ink">
              <Bell size={12} /> Set reminder
            </Link>
            <Button variant="outline" size="sm" className="gap-1.5"
              onClick={() => setEditing(!editing)}>
              <Edit2 size={13} />{editing ? "Cancel" : "Edit"}
            </Button>
            <Button variant="ghost" size="sm"
              className="gap-1 text-red-400 hover:bg-red-50 hover:text-red-600"
              onClick={() => {
                if (!window.confirm("Delete this application?")) return
                deleteApp.mutate(id!, { onSuccess: () => navigate("/applications") })
              }}>
              <Trash2 size={13} />
            </Button>
          </div>
        </div>

        {/* Pipeline stepper */}
        <div className="mt-6">
          <PipelineStepper current={app.status}
            onSelect={(s) => s !== app.status && updateApp.mutate({ id: id!, body: { status: s } })} />
        </div>

        {/* Meta strip */}
        <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 border-t border-border pt-5 text-xs">
          {[
            { icon: Calendar,  label: "Applied", value: formatDate(app.applied_date as any) },
            { icon: Briefcase, label: "Source",  value: SOURCE_LABELS[app.source ?? ""] ?? app.source ?? "—" },
            { icon: Clock,     label: "Added",   value: timeAgo(app.created_at) },
            { icon: Globe,     label: "Salary",  value: (app as any).salary_range ?? "Not disclosed" },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="flex items-center gap-1.5 text-ink-muted">
              <Icon size={12} className="text-ink-faint" />
              <span className="text-ink-faint">{label}:</span>
              <span className="font-medium text-ink">{value}</span>
            </div>
          ))}
          {(app as any).job_url && (
            <a href={(app as any).job_url} target="_blank" rel="noreferrer"
              className="flex items-center gap-1 text-ink-muted hover:text-ink">
              <ExternalLink size={12} /> View posting
            </a>
          )}
        </div>
      </div>

      {/* Edit form */}
      {editing && (
        <div className="animate-slide-up rounded-xl border border-ink/10 bg-card p-6">
          <h2 className="mb-5 font-display text-lg text-ink">Edit details</h2>
          <form className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5"><Label>Company</Label><Input {...register("company_name")} /></div>
              <div className="space-y-1.5"><Label>Job title</Label><Input {...register("job_title")} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5"><Label>Location</Label><Input {...register("location")} /></div>
              <div className="space-y-1.5">
                <Label>Work mode</Label>
                <select {...register("work_mode")}
                  className="h-9 w-full rounded-md border border-border bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring">
                  <option value="">—</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="on_site">On-site</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1.5"><Label>Salary min</Label><Input type="number" {...register("salary_min")} /></div>
              <div className="space-y-1.5"><Label>Salary max</Label><Input type="number" {...register("salary_max")} /></div>
              <div className="space-y-1.5"><Label>Currency</Label><Input placeholder="BWP" {...register("salary_currency")} /></div>
            </div>
            <div className="space-y-1.5"><Label>Notes</Label><Textarea rows={4} {...register("notes")} /></div>
            <div className="flex gap-2">
              <Button type="button" disabled={updateApp.isPending} className="gap-2"
                onClick={handleSubmit((d) => {
                  const payload: Record<string, unknown> = Object.fromEntries(
                    Object.entries(d).filter(([, v]) => v !== "" && v !== undefined)
                  )
                  // Coerce salary strings to numbers for the API
                  if (payload.salary_min) payload.salary_min = Number(payload.salary_min)
                  if (payload.salary_max) payload.salary_max = Number(payload.salary_max)
                  updateApp.mutate({ id: id!, body: payload }, { onSuccess: () => setEditing(false) })
                })}>
                {updateApp.isPending && <Loader2 size={14} className="animate-spin" />}
                Save changes
              </Button>
              <Button type="button" variant="outline" onClick={() => { reset(); setEditing(false) }}>Cancel</Button>
            </div>
          </form>
        </div>
      )}

      {/* Notes (read view) */}
      {!editing && (app as any).notes && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-3 font-display text-lg text-ink">Notes</h2>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-muted">{(app as any).notes}</p>
        </div>
      )}

      {/* Documents + History */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 font-display text-lg text-ink">
            Documents
            {documents.length > 0 && (
              <span className="ml-2 rounded-full bg-cream-darker px-2 py-0.5 text-xs font-normal text-ink-muted">
                {documents.length}
              </span>
            )}
          </h2>
          <div className="space-y-2">
            {documents.map((doc: any) => (
              <DocumentRow key={doc.id} doc={doc} applicationId={id!} />
            ))}
          </div>
          <div className="mt-3"><UploadZone applicationId={id!} /></div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 font-display text-lg text-ink">Status history</h2>
          <StatusTimeline applicationId={id!} />
        </div>
      </div>
    </div>
  )
}