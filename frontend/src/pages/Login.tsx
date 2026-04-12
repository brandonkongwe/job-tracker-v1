import { useEffect } from "react"
import { Link, useSearchParams, Navigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Loader2, ArrowRight } from "lucide-react"
import { useLogin } from "@/api/hooks/useAuth"
import { useAuthStore } from "@/stores/authStore"
import { Button } from "@/components/ui/button"
import { Input, Label } from "@/components/ui/index"
import { cn } from "@/lib/utils"

const schema = z.object({
  email:    z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated())
  const [searchParams]  = useSearchParams()
  const justRegistered  = searchParams.get("registered") === "true"

  const login = useLogin()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  if (isAuthenticated) return <Navigate to="/dashboard" replace />

  return (
    <div className="grain flex min-h-screen bg-cream-DEFAULT">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-ink p-12">
        <div>
          <span className="font-display text-2xl text-cream-DEFAULT">
            Job<span className="text-ink-muted">Tracker</span>
          </span>
        </div>

        {/* Pull quote */}
        <div className="animate-fade-in">
          <p className="font-display text-4xl leading-tight text-cream-DEFAULT">
            Keep track of your job applications.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <div className="h-px flex-1 bg-ink-soft" />
            <span className="text-xs tracking-widest text-ink-muted uppercase">
              Stay organised
            </span>
          </div>
        </div>

        {/* Stats strip */}
        <div className="grid grid-cols-3 gap-4 border-t border-ink-soft pt-8">
          {[
            { n: "100%",  label: "Your data, always" },
          ].map(({ n, label }) => (
            <div key={label}>
              <p className="font-display text-3xl text-cream-DEFAULT">{n}</p>
              <p className="mt-1 text-xs text-ink-muted">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex w-full flex-col items-center justify-center px-6 lg:w-1/2 lg:px-16">
        <div className="w-full max-w-sm animate-slide-up">
          {/* Mobile wordmark */}
          <div className="mb-10 lg:hidden">
            <span className="font-display text-2xl text-ink">
              Job<span className="text-ink-muted">Tracker</span>
            </span>
          </div>

          <h1 className="font-display text-3xl text-ink">Welcome back</h1>
          <p className="mt-2 text-sm text-ink-muted">
            Sign in to your account to continue.
          </p>

          {justRegistered && (
            <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              Account created — you can now sign in.
            </div>
          )}

          {login.error && (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {(login.error as any)?.message ?? "Invalid email or password."}
            </div>
          )}

          <form
            onSubmit={handleSubmit((data) => login.mutate(data))}
            className="mt-8 space-y-5"
          >
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                {...register("email")}
                className={cn(errors.email && "border-red-400")}
              />
              {errors.email && (
                <p className="text-xs text-red-600">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                {...register("password")}
                className={cn(errors.password && "border-red-400")}
              />
              {errors.password && (
                <p className="text-xs text-red-600">{errors.password.message}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full gap-2"
              disabled={login.isPending}
            >
              {login.isPending ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <ArrowRight size={16} />
              )}
              {login.isPending ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-ink-muted">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="font-medium text-ink underline underline-offset-4 hover:text-ink-soft"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}