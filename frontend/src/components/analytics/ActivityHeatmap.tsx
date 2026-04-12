/* need to fix this */

import { useMemo } from "react"
import { cn } from "@/lib/utils"

interface HeatmapDay {
  date:  string
  count: number
}

interface Props {
  data: HeatmapDay[]
}

function getIntensity(count: number, max: number): number {
  if (count === 0 || max === 0) return 0
  return Math.ceil((count / max) * 4)
}

const INTENSITY_CLASSES = [
  "bg-cream-darker",           // 0 — empty
  "bg-amber-100",              // 1
  "bg-amber-300",              // 2
  "bg-amber-500",              // 3
  "bg-amber-700",              // 4 — peak
]

const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]

export function ActivityHeatmap({ data }: Props) {
  const max = useMemo(() => Math.max(...data.map((d) => d.count), 1), [data])

  // Group into weeks (columns of 7)
  const weeks = useMemo(() => {
    const chunks: HeatmapDay[][] = []
    for (let i = 0; i < data.length; i += 7) {
      chunks.push(data.slice(i, i + 7))
    }
    return chunks
  }, [data])

  // Show month labels at the start of each month
  const monthLabels = useMemo(() => {
    const labels: { weekIdx: number; label: string }[] = []
    weeks.forEach((week, wi) => {
      const firstDay = week[0]
      if (!firstDay) return
      const date = new Date(firstDay.date)
      if (date.getDate() <= 7) {
        labels.push({
          weekIdx: wi,
          label: date.toLocaleDateString("en-US", { month: "short" }),
        })
      }
    })
    return labels
  }, [weeks])

  return (
    <div className="space-y-2">
      {/* Month labels */}
      <div className="relative ml-6 flex">
        {monthLabels.map(({ weekIdx, label }) => (
          <div
            key={`${weekIdx}-${label}`}
            className="absolute text-[10px] text-ink-faint"
            style={{ left: `${(weekIdx / weeks.length) * 100}%` }}
          >
            {label}
          </div>
        ))}
      </div>

      <div className="flex gap-1">
        {/* Day-of-week labels */}
        <div className="flex flex-col gap-0.5 pr-1">
          {DAY_LABELS.map((d, i) => (
            <div key={i} className="h-3 text-[10px] leading-3 text-ink-faint">
              {d}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="flex gap-0.5 overflow-hidden">
          {weeks.map((week, wi) => (
            <div key={wi} className="flex flex-col gap-0.5">
              {week.map((day) => {
                const intensity = getIntensity(day.count, max)
                return (
                  <div
                    key={day.date}
                    title={`${day.date}: ${day.count} application${day.count !== 1 ? "s" : ""}`}
                    className={cn(
                      "h-3 w-3 rounded-sm transition-transform hover:scale-125",
                      INTENSITY_CLASSES[intensity]
                    )}
                  />
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="ml-6 flex items-center gap-1.5 text-[10px] text-ink-faint">
        <span>Less</span>
        {INTENSITY_CLASSES.map((cls, i) => (
          <div key={i} className={cn("h-3 w-3 rounded-sm", cls)} />
        ))}
        <span>More</span>
      </div>
    </div>
  )
}