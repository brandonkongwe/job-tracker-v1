import { Suspense, lazy } from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { AppShell } from "@/components/layout/AppShell"
import { ProtectedRoute } from "@/components/layout/ProtectedRoute"
import { Loader2 } from "lucide-react"

// Lazy-load pages for code splitting
const LoginPage           = lazy(() => import("@/pages/Login"))
const RegisterPage        = lazy(() => import("@/pages/Register"))
const DashboardPage       = lazy(() => import("@/pages/Dashboard"))
const ApplicationsPage    = lazy(() => import("@/pages/Applications"))
const ApplicationDetail   = lazy(() => import("@/pages/ApplicationDetail"))
const RemindersPage       = lazy(() => import("@/pages/Reminders"))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 30, // 30 seconds default
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
})

function PageLoader() {
  return (
    <div className="flex h-full min-h-[400px] items-center justify-center">
      <Loader2 size={24} className="animate-spin text-ink-faint" />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected routes — all wrapped in AppShell sidebar */}
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard"              element={<DashboardPage />} />
              <Route path="/applications"           element={<ApplicationsPage />} />
              <Route path="/applications/:id"       element={<ApplicationDetail />} />
              <Route path="/reminders"              element={<RemindersPage />} />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}