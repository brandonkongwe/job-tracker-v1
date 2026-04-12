import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Plus, Loader2, X } from "lucide-react"
import { useCreateApplication } from "@/api/hooks/useApplications"
import { Button } from "@/components/ui/button"
import { Input, Label, Textarea } from "@/components/ui/index"
import { cn } from "@/lib/utils"

const schema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  job_title:    z.string().min(1, "Job title is required"),
  job_url:      z.string().url("Enter a valid URL").or(z.literal("")).optional(),
  location:     z.string().optional(),
  work_mode:    z.enum(["remote", "hybrid", "on_site", ""]).optional(),
  status:       z.enum(["saved", "applied", "screening", "interview", "offer", "accepted", "rejected", "withdrawn"]),
  applied_date: z.string().optional(),
  source:       z.string().optional(),
  salary_min:   z.coerce.number().positive().optional().or(z.literal("")),
  salary_max:   z.coerce.number().positive().optional().or(z.literal("")),
  notes:        z.string().optional(),
})

type FormData = z.infer<typeof schema>

export function CreateApplicationDialog() {
  const [open, setOpen] = useState(false)
  const create = useCreateApplication()

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema) as any,
    defaultValues: { status: "saved" } as FormData,
  })

  const status = watch("status")

  const onSubmit = async (data: FormData) => {
    // Strip empty strings before sending
    const payload = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "" && v !== undefined)
    )
    return new Promise<void>((resolve) => {
      create.mutate(payload, {
        onSuccess: () => {
          reset()
          setOpen(false)
          resolve()
        },
      })
    })
  }

  if (!open) {
    return (
      <Button onClick={() => setOpen(true)} className="gap-2">
        <Plus size={16} />
        Add application
      </Button>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 backdrop-blur-sm">
      <div className="animate-slide-up relative w-full max-w-lg rounded-xl border border-border bg-cream-DEFAULT shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="font-display text-xl text-ink">New application</h2>
          <button
            onClick={() => { reset(); setOpen(false) }}
            className="rounded-md p-1 text-ink-faint hover:text-ink"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="max-h-[70vh] overflow-y-auto px-6 py-5">
          <div className="space-y-4">
            {/* Company + Title */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="company_name">Company *</Label>
                <Input
                  id="company_name"
                  placeholder="Acme Corp"
                  {...register("company_name")}
                  className={cn(errors.company_name && "border-red-400")}
                />
                {errors.company_name && (
                  <p className="text-xs text-red-600">{errors.company_name.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="job_title">Job title *</Label>
                <Input
                  id="job_title"
                  placeholder="Data Engineer"
                  {...register("job_title")}
                  className={cn(errors.job_title && "border-red-400")}
                />
                {errors.job_title && (
                  <p className="text-xs text-red-600">{errors.job_title.message}</p>
                )}
              </div>
            </div>

            {/* Status + Applied date */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="status">Status *</Label>
                <select
                  id="status"
                  {...register("status")}
                  className="h-9 w-full rounded-md border border-border bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  {[
                    ["saved", "Saved"],
                    ["applied", "Applied"],
                    ["screening", "Screening"],
                    ["interview", "Interview"],
                    ["offer", "Offer"],
                    ["accepted", "Accepted"],
                    ["rejected", "Rejected"],
                    ["withdrawn", "Withdrawn"],
                  ].map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="applied_date">
                  Applied date{status !== "saved" && " *"}
                </Label>
                <Input
                  id="applied_date"
                  type="date"
                  {...register("applied_date")}
                  className={cn(errors.applied_date && "border-red-400")}
                />
              </div>
            </div>

            {/* Location + Work mode */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="location">Location</Label>
                <Input id="location" placeholder="Gaborone, BW" {...register("location")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="work_mode">Work mode</Label>
                <select
                  id="work_mode"
                  {...register("work_mode")}
                  className="h-9 w-full rounded-md border border-border bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">Select…</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="on_site">On-site</option>
                </select>
              </div>
            </div>

            {/* URL + Source */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="job_url">Job posting URL</Label>
                <Input id="job_url" type="url" placeholder="https://…" {...register("job_url")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="source">Found via</Label>
                <select
                  id="source"
                  {...register("source")}
                  className="h-9 w-full rounded-md border border-border bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">Select…</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="indeed">Indeed</option>
                  <option value="company">Company Website</option>
                  <option value="referral">Referral</option>
                  <option value="recruiter">Recruiter</option>
                  <option value="job_board">Job Board</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            {/* Salary */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="salary_min">Salary min</Label>
                <Input
                  id="salary_min"
                  type="number"
                  placeholder="50,000"
                  {...register("salary_min")}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="salary_max">Salary max</Label>
                <Input
                  id="salary_max"
                  type="number"
                  placeholder="80,000"
                  {...register("salary_max")}
                />
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-1.5">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                placeholder="Recruiter name, interview format, any context…"
                rows={3}
                {...register("notes")}
              />
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-t border-border px-6 py-4">
          <Button variant="outline" onClick={() => { reset(); setOpen(false) }}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit(onSubmit)}
            disabled={create.isPending}
            className="gap-2"
          >
            {create.isPending && <Loader2 size={14} className="animate-spin" />}
            Save application
          </Button>
        </div>
      </div>
    </div>
  )
}