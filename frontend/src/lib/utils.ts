import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, formatDistanceToNow } from "date-fns"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
 
export function formatDate(date: string | null | undefined): string {
  if (!date) return "—"
  return format(new Date(date), "dd MMM yyyy")
}
 
export function formatDateTime(date: string | null | undefined): string {
  if (!date) return "—"
  return format(new Date(date), "dd MMM yyyy, HH:mm")
}
 
export function timeAgo(date: string | null | undefined): string {
  if (!date) return "—"
  return formatDistanceToNow(new Date(date), { addSuffix: true })
}
 
export function formatCurrency(
  amount: number | null | undefined,
  currency = "BWP"
): string {
  if (!amount) return "—"
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}
 
/** Map status value to display config */
export const STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; dot: string }
> = {
  saved:     { label: "Saved",     bg: "bg-[#e8e4dc]", text: "text-[#6b6560]", dot: "bg-[#a09b94]" },
  applied:   { label: "Applied",   bg: "bg-blue-100",  text: "text-blue-700",  dot: "bg-blue-500"  },
  screening: { label: "Screening", bg: "bg-purple-100",text: "text-purple-700",dot: "bg-purple-500"},
  interview: { label: "Interview", bg: "bg-amber-100", text: "text-amber-700", dot: "bg-amber-500" },
  offer:     { label: "Offer",     bg: "bg-emerald-100",text:"text-emerald-700",dot:"bg-emerald-500"},
  accepted:  { label: "Accepted",  bg: "bg-emerald-900",text:"text-emerald-300",dot:"bg-emerald-400"},
  rejected:  { label: "Rejected",  bg: "bg-red-100",   text: "text-red-700",   dot: "bg-red-500"   },
  withdrawn: { label: "Withdrawn", bg: "bg-gray-100",  text: "text-gray-600",  dot: "bg-gray-400"  },
}
 
export const PIPELINE_STAGES = [
  "saved", "applied", "screening", "interview", "offer", "accepted",
] as const
 
export const WORK_MODE_LABELS: Record<string, string> = {
  remote:  "Remote",
  hybrid:  "Hybrid",
  on_site: "On-site",
}
 
export const SOURCE_LABELS: Record<string, string> = {
  linkedin:  "LinkedIn",
  indeed:    "Indeed",
  company:   "Company Website",
  referral:  "Referral",
  recruiter: "Recruiter",
  job_board: "Job Board",
  other:     "Other",
}
