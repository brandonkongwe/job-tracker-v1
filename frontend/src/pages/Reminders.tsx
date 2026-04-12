import { useState } from "react"
import { useLocation } from "react-router-dom"
import { Bell, Plus, Loader2, Check, X, Calendar, Clock } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { apiClient } from "@/api/client"
import { useApplications } from "@/api/hooks/useApplications"
import { Button } from "@/components/ui/button"
import { Input, Label, Textarea } from "@/components/ui/index"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { formatDateTime, timeAgo, cn } from "@/lib/utils"

// Hooks
function useReminders(filters: { is_sent?: boolean; is_active?: boolean } = {}) {
  return useQuery({
    queryKey: ["reminders", filters],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/v1/reminders/", {
        params: { query: filters as any },
      })
      if (error) throw error
      return data!
    },
  })
}

function useCreateReminder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const { data, error } = await apiClient.POST("/api/v1/reminders/", { body: body as any })
      if (error) throw error
      return data!
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  })
}

function useCancelReminder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const { data, error } = await apiClient.POST(
        "/api/v1/reminders/{id}/cancel/" as any,
        { params: { path: { id } } } as any
      )
      if (error) throw error
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  })
}

function useDeleteReminder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await apiClient.DELETE("/api/v1/reminders/{id}/", {
        params: { path: { id } },
      })
      if (error) throw error
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  })
}

// Create form schema
const schema = z.object({
  application:   z.string().min(1, "Select an application"),
  reminder_type: z.enum(["follow_up","interview_prep","deadline","general"]),
  remind_at:     z.string().min(1, "Set a date and time"),
  message:       z.string().optional(),
})
type FormData = z.infer<typeof schema>

const REMINDER_TYPE_LABELS: Record<string, string> = {
  follow_up:      "Follow Up",
  interview_prep: "Interview Prep",
  deadline:       "Deadline",
  general:        "General",
}
const REMINDER_TYPE_COLORS: Record<string, string> = {
  follow_up:      "bg-blue-100 text-blue-700",
  interview_prep: "bg-amber-100 text-amber-700",
  deadline:       "bg-red-100 text-red-700",
  general:        "bg-gray-100 text-gray-600",
}

// Reminder card
function ReminderCard({ reminder }: { reminder: any }) {
  const cancel = useCancelReminder()
  const remove = useDeleteReminder()
  const isOverdue = !reminder.is_sent && reminder.is_active &&
    new Date(reminder.remind_at) < new Date()

  return (
    <div className={cn(
      "rounded-lg border p-4 transition-all",
      reminder.is_sent     && "border-border bg-cream-darker/40 opacity-60",
      !reminder.is_sent && !isOverdue && "border-border bg-card",
      isOverdue            && "border-amber-200 bg-amber-50",
      !reminder.is_active && !reminder.is_sent && "border-border bg-cream-darker/40 opacity-50"
    )}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {/* Type badge */}
          <div className="mb-2 flex items-center gap-2">
            <span className={cn(
              "rounded-full px-2 py-0.5 text-xs font-medium",
              REMINDER_TYPE_COLORS[reminder.reminder_type] ?? "bg-gray-100 text-gray-600"
            )}>
              {REMINDER_TYPE_LABELS[reminder.reminder_type] ?? reminder.reminder_type}
            </span>
            {reminder.is_sent && (
              <span className="flex items-center gap-1 text-xs text-emerald-600">
                <Check size={11} /> Sent {timeAgo(reminder.sent_at)}
              </span>
            )}
            {isOverdue && (
              <span className="text-xs font-medium text-amber-700">Overdue</span>
            )}
            {!reminder.is_active && !reminder.is_sent && (
              <span className="text-xs text-ink-faint">Cancelled</span>
            )}
          </div>

          {/* Application name */}
          <p className="font-medium text-ink">
            {reminder.job_title} at {reminder.company_name}
          </p>

          {/* Remind at */}
          <div className="mt-1 flex items-center gap-1.5 text-xs text-ink-muted">
            <Clock size={11} />
            {reminder.is_sent ? "Was due" : "Due"}{" "}
            {formatDateTime(reminder.remind_at)}
          </div>

          {/* Message */}
          {reminder.message && (
            <p className="mt-2 rounded-md bg-cream-darker px-3 py-2 text-xs text-ink-muted">
              {reminder.message}
            </p>
          )}
        </div>

        {/* Actions */}
        {!reminder.is_sent && reminder.is_active && (
          <div className="flex shrink-0 items-center gap-1">
            <button
              onClick={() => cancel.mutate(reminder.id)}
              disabled={cancel.isPending}
              className="rounded p-1.5 text-xs text-ink-faint hover:bg-cream-darker hover:text-ink"
              title="Cancel reminder"
            >
              <X size={14} />
            </button>
          </div>
        )}
        {(reminder.is_sent || !reminder.is_active) && (
          <button
            onClick={() => remove.mutate(reminder.id)}
            disabled={remove.isPending}
            className="shrink-0 rounded p-1.5 text-ink-faint hover:bg-cream-darker hover:text-red-500"
            title="Delete reminder"
          >
            <X size={14} />
          </button>
        )}
      </div>
    </div>
  )
}

// Main page
export default function RemindersPage() {
  const location = useLocation()
  const prefillAppId = (location.state as any)?.prefillApplicationId ?? ""
  const [showForm, setShowForm] = useState(!!prefillAppId)
  const [tab, setTab] = useState<"upcoming"|"sent">("upcoming")

  const upcoming = useReminders({ is_active: true,  is_sent: false })
  const sent     = useReminders({ is_sent: true })
  const create   = useCreateReminder()
  const { data: appsData } = useApplications({ page_size: 100, is_active: true })
  const apps = (appsData?.results as any[]) ?? []

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      application: prefillAppId,
      reminder_type: "general",
    },
  })

  const onSubmit = (data: FormData) => {
    // Convert local datetime-local input to ISO UTC string
    const remindAt = new Date(data.remind_at).toISOString()
    create.mutate(
      { ...data, remind_at: remindAt },
      { onSuccess: () => { reset(); setShowForm(false) } }
    )
  }

  const upcomingList = (upcoming.data?.results as any[]) ?? []
  const sentList     = (sent.data?.results as any[]) ?? []

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Bell size={20} className="text-ink-muted" />
            <h1 className="font-display text-2xl text-ink">Reminders</h1>
          </div>
          <p className="mt-0.5 text-sm text-ink-muted">
            {upcomingList.length} upcoming · {sentList.length} sent
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} className="gap-2" size="sm">
          <Plus size={15} />
          {showForm ? "Cancel" : "New reminder"}
        </Button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="animate-slide-up rounded-xl border border-ink/10 bg-card p-6">
          <h2 className="mb-5 font-display text-lg text-ink">New reminder</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label>Application *</Label>
              <select {...register("application")}
                className={cn(
                  "h-9 w-full rounded-md border bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring",
                  errors.application ? "border-red-400" : "border-border"
                )}>
                <option value="">Select an application…</option>
                {apps.map((app: any) => (
                  <option key={app.id} value={app.id}>
                    {app.job_title} at {app.company_name}
                  </option>
                ))}
              </select>
              {errors.application && <p className="text-xs text-red-600">{errors.application.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Type</Label>
                <select {...register("reminder_type")}
                  className="h-9 w-full rounded-md border border-border bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring">
                  <option value="general">General</option>
                  <option value="follow_up">Follow Up</option>
                  <option value="interview_prep">Interview Prep</option>
                  <option value="deadline">Deadline</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Date & time *</Label>
                <Input
                  type="datetime-local"
                  {...register("remind_at")}
                  min={new Date().toISOString().slice(0, 16)}
                  className={cn(errors.remind_at && "border-red-400")}
                />
                {errors.remind_at && <p className="text-xs text-red-600">{errors.remind_at.message}</p>}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Message <span className="text-ink-faint">(optional)</span></Label>
              <Textarea
                rows={3}
                placeholder="Included in the reminder email…"
                {...register("message")}
              />
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={create.isPending} className="gap-2">
                {create.isPending && <Loader2 size={14} className="animate-spin" />}
                Save reminder
              </Button>
              <Button type="button" variant="outline" onClick={() => { reset(); setShowForm(false) }}>
                Cancel
              </Button>
            </div>

            {create.error && (
              <p className="text-xs text-red-600">
                {(create.error as any)?.remind_at?.[0] ??
                 (create.error as any)?.application?.[0] ??
                 "Something went wrong."}
              </p>
            )}
          </form>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-border bg-cream-darker p-1">
        {(["upcoming","sent"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={cn(
              "flex-1 rounded-md py-1.5 text-sm font-medium capitalize transition-all",
              tab === t ? "bg-card text-ink shadow-sm" : "text-ink-muted hover:text-ink"
            )}>
            {t}
            <span className="ml-1.5 rounded-full bg-cream-darker px-1.5 py-0.5 text-xs">
              {t === "upcoming" ? upcomingList.length : sentList.length}
            </span>
          </button>
        ))}
      </div>

      {/* List */}
      {(tab === "upcoming" ? upcoming : sent).isPending ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={20} className="animate-spin text-ink-faint" />
        </div>
      ) : (tab === "upcoming" ? upcomingList : sentList).length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border py-16 text-center">
          <Bell size={28} className="text-ink-faint" />
          <p className="font-medium text-ink">
            {tab === "upcoming" ? "No upcoming reminders" : "No sent reminders"}
          </p>
          <p className="text-sm text-ink-muted">
            {tab === "upcoming" ? "Create one to get email nudges." : "Sent reminders will appear here."}
          </p>
        </div>
      ) : (
        <div className="space-y-3 animate-fade-in">
          {(tab === "upcoming" ? upcomingList : sentList).map((r: any) => (
            <ReminderCard key={r.id} reminder={r} />
          ))}
        </div>
      )}
    </div>
  )
}