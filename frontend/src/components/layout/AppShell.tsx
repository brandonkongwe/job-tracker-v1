import { NavLink, Outlet, useNavigate } from "react-router-dom"
import {
  LayoutDashboard,
  Briefcase,
  Bell,
  LogOut,
  User,
  ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/stores/authStore"
import { useLogout } from "@/api/hooks/useAuth"
import { Button } from "@/components/ui/button"

const NAV_ITEMS = [
  { to: "/dashboard",    icon: LayoutDashboard, label: "Dashboard"    },
  { to: "/applications", icon: Briefcase,       label: "Applications" },
  { to: "/reminders",    icon: Bell,            label: "Reminders"    },
]

export function AppShell() {
  const user   = useAuthStore((s) => s.user)
  const logout = useLogout()

  return (
    <div className="flex h-screen overflow-hidden bg-cream-DEFAULT">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-border bg-cream-dark">
        {/* Wordmark */}
        <div className="flex h-16 items-center border-b border-border px-5">
          <span className="font-display text-lg text-ink">
            Job<span className="text-ink-muted">Tracker</span>
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-0.5 px-2 py-4">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-all",
                  isActive
                    ? "bg-ink text-cream-DEFAULT font-medium"
                    : "text-ink-muted hover:bg-cream-darker hover:text-ink"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    size={16}
                    className={cn(
                      "shrink-0 transition-colors",
                      isActive ? "text-cream-DEFAULT" : "text-ink-faint group-hover:text-ink-muted"
                    )}
                  />
                  {label}
                  {isActive && (
                    <ChevronRight size={12} className="ml-auto text-cream-darker opacity-60" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t border-border p-3">
          <div className="mb-2 flex items-center gap-3 rounded-md px-2 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink text-xs font-medium text-cream-DEFAULT">
              {user?.full_name?.charAt(0) ?? "?"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-ink">{user?.full_name}</p>
              <p className="truncate text-[10px] text-ink-faint">{user?.role?.replace("_", " ")}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-ink-muted hover:text-ink"
            onClick={() => logout.mutate()}
          >
            <LogOut size={14} />
            Sign out
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}