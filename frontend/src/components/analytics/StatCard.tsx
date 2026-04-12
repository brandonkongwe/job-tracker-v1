import { cn } from "@/lib/utils"

interface StatCardProps {
  label:     string
  value:     string | number
  sub?:      string
  accent?:   boolean
  className?: string
}

export function StatCard({ label, value, sub, accent, className }: StatCardProps) {
  return (
    <div className={cn(
      "rounded-xl border border-border p-5",
      accent ? "bg-ink text-cream-DEFAULT" : "bg-card",
      className
    )}>
      <p className={cn("text-xs font-medium uppercase tracking-wider",
        accent ? "text-cream-darker" : "text-ink-faint")}>
        {label}
      </p>
      <p className={cn("mt-2 font-display text-4xl",
        accent ? "text-cream-DEFAULT" : "text-ink")}>
        {value}
      </p>
      {sub && (
        <p className={cn("mt-1 text-xs", accent ? "text-cream-dark" : "text-ink-faint")}>
          {sub}
        </p>
      )}
    </div>
  )
}