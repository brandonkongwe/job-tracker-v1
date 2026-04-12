import { LayoutDashboard, Loader2, TrendingUp, Target, Clock } from "lucide-react"
import {
  AreaChart, Area, BarChart, Bar, FunnelChart, Funnel,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, LabelList,
} from "recharts"
import {
  useDashboard, useWeeklyVolume, useConversionFunnel,
  useStageDuration, useActivityHeatmap,
} from "@/api/hooks/useAnalytics"
import { StatCard } from "@/components/analytics/StatCard"
import { ActivityHeatmap } from "@/components/analytics/ActivityHeatmap"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { useAuthStore } from "@/stores/authStore"
import { cn } from "@/lib/utils"

const CHART_COLORS = {
  primary:   "#1a1814",
  secondary: "#a09b94",
  amber:     "#d97706",
  teal:      "#0d9488",
  coral:     "#e05a3a",
  muted:     "#e0dbd0",
}

const STATUS_CHART_COLORS: Record<string, string> = {
  saved:     "#a09b94",
  applied:   "#3b82f6",
  screening: "#8b5cf6",
  interview: "#f59e0b",
  offer:     "#10b981",
  accepted:  "#065f46",
  rejected:  "#ef4444",
  withdrawn: "#9ca3af",
}

// Custom tooltip
function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-lg">
      <p className="text-xs text-ink-faint">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} className="text-sm font-medium text-ink">
          {p.value} {p.name ?? ""}
        </p>
      ))}
    </div>
  )
}

// Section wrapper
function Section({ title, icon: Icon, children, className }: {
  title: string; icon: any; children: React.ReactNode; className?: string
}) {
  return (
    <div className={cn("rounded-xl border border-border bg-card p-6", className)}>
      <div className="mb-5 flex items-center gap-2">
        <Icon size={15} className="text-ink-faint" />
        <h2 className="font-display text-lg text-ink">{title}</h2>
      </div>
      {children}
    </div>
  )
}

// Main dashboard
export default function DashboardPage() {
  const user      = useAuthStore((s) => s.user)
  const dashboard = useDashboard()
  const volume    = useWeeklyVolume(12)
  const funnel    = useConversionFunnel()
  const duration  = useStageDuration()
  const heatmap   = useActivityHeatmap()

  const loading = dashboard.isPending

  if (loading) return (
    <div className="flex h-full items-center justify-center py-32">
      <Loader2 size={24} className="animate-spin text-ink-faint" />
    </div>
  )

  const d            = dashboard.data as any
  const total        = d?.total_applications ?? 0
  const active       = d?.active_applications ?? 0
  const rr           = d?.response_rate ?? {}
  const statusBreak  = (d?.status_breakdown ?? []).filter((s: any) => s.count > 0)
  const topCompanies = d?.top_companies ?? []
  const sources      = d?.source_breakdown ?? []
  const weeklyData   = (volume.data as any[]) ?? []
  const funnelData   = (funnel.data as any[]) ?? []
  const durationData = (duration.data as any[]) ?? []
  const heatmapData  = (heatmap.data as any[]) ?? []

  return (
    <div className="space-y-6 p-8 animate-fade-in">
      {/* Page title */}
      <div>
        <div className="flex items-center gap-2">
          <LayoutDashboard size={20} className="text-ink-muted" />
          <h1 className="font-display text-2xl text-ink">Dashboard</h1>
        </div>
        <p className="mt-0.5 text-sm text-ink-muted">
          {/* i have no idea */}
          Welcome back{user?.first_name ? `, ${user.first_name}` : ""}.
          {total > 0
            ? ` You have ${active} active application${active !== 1 ? "s" : ""}.`
            : " Add your first application to get started."}
        </p>
      </div>

      {/* Top stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total applications" value={total} accent />
        <StatCard
          label="Active"
          value={active}
          sub={total > 0 ? `${Math.round((active / total) * 100)}% of total` : undefined}
        />
        <StatCard
          label="Response rate"
          value={`${rr.response_rate ?? 0}%`}
          sub={`${rr.responded ?? 0} of ${rr.total ?? 0} responded`}
        />
        <StatCard
          label="Interview rate"
          value={`${rr.interview_rate ?? 0}%`}
          sub={`${rr.offer_rate ?? 0}% offer rate`}
        />
      </div>

      {/* Weekly volume chart */}
      <Section title="Application volume" icon={TrendingUp}>
        {weeklyData.length === 0 ? (
          <p className="py-8 text-center text-sm text-ink-faint">No data yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={weeklyData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
              <defs>
                <linearGradient id="volumeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={CHART_COLORS.primary} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0}    />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.muted} vertical={false} />
              <XAxis
                dataKey="week"
                tick={{ fontSize: 10, fill: CHART_COLORS.secondary }}
                tickFormatter={(v) => v.split("-W")[1] ? `W${v.split("-W")[1]}` : v}
                axisLine={false} tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: CHART_COLORS.secondary }}
                axisLine={false} tickLine={false} allowDecimals={false}
              />
              <Tooltip content={<ChartTooltip />} />
              <Area
                type="monotone" dataKey="count" name="Applications"
                stroke={CHART_COLORS.primary} strokeWidth={2}
                fill="url(#volumeGrad)" dot={false} activeDot={{ r: 4 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </Section>

      {/* Status breakdown + Sources */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Status bar chart */}
        <Section title="By status" icon={Target}>
          {statusBreak.length === 0 ? (
            <p className="py-8 text-center text-sm text-ink-faint">No data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={statusBreak}
                layout="vertical"
                margin={{ top: 0, right: 32, bottom: 0, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.muted} horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: CHART_COLORS.secondary }}
                  axisLine={false} tickLine={false} allowDecimals={false} />
                <YAxis type="category" dataKey="label" width={72}
                  tick={{ fontSize: 11, fill: CHART_COLORS.secondary }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" name="Applications" radius={[0, 4, 4, 0]}>
                  {statusBreak.map((entry: any) => (
                    <Cell key={entry.status} fill={STATUS_CHART_COLORS[entry.status] ?? CHART_COLORS.secondary} />
                  ))}
                  <LabelList dataKey="count" position="right"
                    style={{ fontSize: 11, fill: CHART_COLORS.secondary }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Section>

        {/* Source breakdown */}
        <Section title="By source" icon={Target}>
          {sources.length === 0 ? (
            <p className="py-8 text-center text-sm text-ink-faint">No data yet.</p>
          ) : (
            <div className="space-y-3">
              {sources.map((src: any) => {
                const pct = total > 0 ? Math.round((src.count / total) * 100) : 0
                return (
                  <div key={src.source}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="text-ink">{src.label}</span>
                      <span className="font-medium text-ink-muted">{src.count} ({pct}%)</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-cream-darker">
                      <div
                        className="h-1.5 rounded-full bg-ink transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Section>
      </div>

      {/* Conversion funnel */}
      <Section title="Conversion funnel" icon={Target}>
        {funnelData.filter((f: any) => f.count > 0).length === 0 ? (
          <p className="py-8 text-center text-sm text-ink-faint">
            Not enough data yet — funnel appears once you have applications across stages.
          </p>
        ) : (
          <div className="space-y-2">
            {funnelData.filter((f: any) => f.count > 0).map((stage: any, i: number) => {
              const topCount = funnelData.find((f: any) => f.count > 0)?.count ?? 1
              const width    = Math.max((stage.count / topCount) * 100, 4)
              return (
                <div key={stage.stage} className="flex items-center gap-4"
                  style={{ animationDelay: `${i * 60}ms` }}>
                  <div className="w-20 shrink-0 text-right text-xs text-ink-muted">{stage.label}</div>
                  <div className="flex-1">
                    <div
                      className="flex items-center gap-2 rounded-r-md py-2 pl-3 pr-4 transition-all duration-700"
                      style={{
                        width: `${width}%`,
                        background: `${STATUS_CHART_COLORS[stage.stage]}22`,
                        borderLeft: `3px solid ${STATUS_CHART_COLORS[stage.stage]}`,
                      }}
                    >
                      <span className="text-xs font-medium text-ink">{stage.count}</span>
                      <span className="text-xs text-ink-faint">{stage.rate}%</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Section>

      {/* Stage duration + Top companies */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Stage duration */}
        <Section title="Avg. days between stages" icon={Clock}>
          {durationData.length === 0 ? (
            <p className="py-8 text-center text-sm text-ink-faint">
              Appears after status transitions are recorded.
            </p>
          ) : (
            <div className="space-y-3">
              {durationData.map((entry: any) => (
                <div key={entry.label} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-ink">{entry.label}</p>
                    <p className="text-xs text-ink-faint">{entry.sample_size} transitions</p>
                  </div>
                  <div className="text-right">
                    <p className="font-display text-2xl text-ink">{entry.avg_days}</p>
                    <p className="text-xs text-ink-faint">days avg.</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* Top companies */}
        <Section title="Top companies" icon={Target}>
          {topCompanies.length === 0 ? (
            <p className="py-8 text-center text-sm text-ink-faint">No data yet.</p>
          ) : (
            <div className="space-y-2.5">
              {topCompanies.map((co: any, i: number) => (
                <div key={co.company_name} className="flex items-center gap-3">
                  <span className="w-5 shrink-0 text-xs font-medium text-ink-faint">
                    {i + 1}
                  </span>
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-cream-darker text-xs font-semibold text-ink-soft">
                    {co.company_name.charAt(0)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">{co.company_name}</p>
                  </div>
                  <span className="text-sm font-medium text-ink-muted">{co.count}</span>
                </div>
              ))}
            </div>
          )}
        </Section>
      </div>

      {/* Activity heatmap */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp size={15} className="text-ink-faint" />
            <h2 className="font-display text-lg text-ink">Activity</h2>
          </div>
          <p className="text-xs text-ink-faint">Last 365 days</p>
        </div>
        {heatmapData.length > 0 ? (
          <div className="overflow-x-auto">
            <ActivityHeatmap data={heatmapData} />
          </div>
        ) : (
          <p className="py-4 text-center text-sm text-ink-faint">No activity data yet.</p>
        )}
      </div>
    </div>
  )
}