import { Link, Navigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Loader2, ArrowRight, Check } from "lucide-react"
import { useRegister } from "@/api/hooks/useAuth"
import { useAuthStore } from "@/stores/authStore"
import { Button } from "@/components/ui/button"
import { Input, Label } from "@/components/ui/index"
import { cn } from "@/lib/utils"

const schema = z
  .object({
    first_name:       z.string().min(1, "First name is required"),
    last_name:        z.string().min(1, "Last name is required"),
    email:            z.string().email("Enter a valid email address"),
    password:         z.string().min(8, "Password must be at least 8 characters"),
    password_confirm: z.string().min(1, "Please confirm your password"),
  })
  .refine((d) => d.password === d.password_confirm, {
    message: "Passwords do not match",
    path:    ["password_confirm"],
  })

type FormData = z.infer<typeof schema>

const PERKS = [
  "Track every application in one place",
  "Automated email reminders",
  "Analytics dashboard & conversion funnel",
  "CV upload per application",
]

export default function RegisterPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated())
  const register_       = useRegister()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  if (isAuthenticated) return <Navigate to="/dashboard" replace />

  const getFieldError = (field: keyof FormData) => errors[field]?.message

  return (
    <div className="grain flex min-h-screen bg-cream-DEFAULT">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-2/5 flex-col justify-between bg-ink p-12">
        <span className="font-display text-2xl text-cream-DEFAULT">
          Job<span className="text-ink-muted">Tracker</span>
        </span>

        <div className="animate-fade-in space-y-6">
          <h2 className="font-display text-3xl leading-tight text-cream-DEFAULT">
            Everything you need to run a{" "}
            <em className="text-ink-muted">disciplined job search.</em>
          </h2>
          <ul className="space-y-3">
            {PERKS.map((perk) => (
              <li key={perk} className="flex items-center gap-3 text-sm text-cream-dark">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-ink-soft">
                  <Check size={10} className="text-cream-DEFAULT" />
                </span>
                {perk}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-ink-muted">
          Text
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex w-full flex-col items-center justify-center px-6 py-12 lg:w-3/5 lg:px-16">
        <div className="w-full max-w-md animate-slide-up">
          <div className="mb-8 lg:hidden">
            <span className="font-display text-2xl text-ink">
              Job<span className="text-ink-muted">Tracker</span>
            </span>
          </div>

          <h1 className="font-display text-3xl text-ink">Create your account</h1>
          <p className="mt-2 text-sm text-ink-muted">
            Start tracking your job search in minutes.
          </p>

          {register_.error && (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {(register_.error as any)?.email?.[0] ??
                (register_.error as any)?.detail ??
                "Something went wrong. Please try again."}
            </div>
          )}

          <form
            onSubmit={handleSubmit((data) => register_.mutate(data))}
            className="mt-8 space-y-5"
          >
            {/* Name row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="first_name">First name</Label>
                <Input
                  id="first_name"
                  placeholder="John"
                  autoComplete="given-name"
                  {...register("first_name")}
                  className={cn(getFieldError("first_name") && "border-red-400")}
                />
                {getFieldError("first_name") && (
                  <p className="text-xs text-red-600">{getFieldError("first_name")}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="last_name">Last name</Label>
                <Input
                  id="last_name"
                  placeholder="Doe"
                  autoComplete="family-name"
                  {...register("last_name")}
                  className={cn(getFieldError("last_name") && "border-red-400")}
                />
                {getFieldError("last_name") && (
                  <p className="text-xs text-red-600">{getFieldError("last_name")}</p>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                {...register("email")}
                className={cn(getFieldError("email") && "border-red-400")}
              />
              {getFieldError("email") && (
                <p className="text-xs text-red-600">{getFieldError("email")}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Min. 8 characters"
                autoComplete="new-password"
                {...register("password")}
                className={cn(getFieldError("password") && "border-red-400")}
              />
              {getFieldError("password") && (
                <p className="text-xs text-red-600">{getFieldError("password")}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password_confirm">Confirm password</Label>
              <Input
                id="password_confirm"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                {...register("password_confirm")}
                className={cn(getFieldError("password_confirm") && "border-red-400")}
              />
              {getFieldError("password_confirm") && (
                <p className="text-xs text-red-600">{getFieldError("password_confirm")}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full gap-2"
              disabled={register_.isPending}
            >
              {register_.isPending ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <ArrowRight size={16} />
              )}
              {register_.isPending ? "Creating account…" : "Create account"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-ink-muted">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-medium text-ink underline underline-offset-4 hover:text-ink-soft"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}