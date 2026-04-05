import { useState } from "react";
import { Eye, EyeOff, Loader2, Lock, Mail } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/context/AuthContext";

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({ email: "", password: "" });

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    try {
      await login(formData);
    } catch {
      setError("Invalid email or password. Please try again.");
    }
  };

  return (
    <div className="min-h-screen px-4 py-6 md:px-8">
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="poster-surface overflow-hidden rounded-[2rem] border border-border/70 px-6 py-8 md:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-foreground/70">Sha8alny</p>
          <p className="type-kicker">Sign in</p>
          <p className="mt-6 text-sm font-semibold text-primary">Welcome back</p>
          <h1 className="mt-4 text-balance text-5xl font-bold md:text-7xl">Return to your career atlas.</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Pick up your roadmap, assessment outcomes, saved jobs, and advisory context without losing track of the bigger journey.
          </p>
          <div className="mt-10 grid gap-4 md:grid-cols-2">
            <div className="atlas-panel p-5">
              <p className="type-kicker">Roadmap</p>
              <p className="mt-3 text-2xl font-bold">Continue where you left off</p>
            </div>
            <div className="atlas-panel p-5">
              <p className="type-kicker">Jobs</p>
              <p className="mt-3 text-2xl font-bold">Keep your saved roles close</p>
            </div>
          </div>
        </section>

        <form className="atlas-panel p-6 md:p-8" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <p className="type-kicker">Account access</p>
            <h2 className="text-4xl font-bold">Sign in</h2>
            <p className="text-sm text-muted-foreground">
              Enter your credentials to access your account.
            </p>
          </div>

          {error ? (
            <div className="mt-5 rounded-[1.25rem] border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
              {error}
            </div>
          ) : null}

          <div className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-10"
                  disabled={isLoading}
                  id="email"
                  onChange={(event) => setFormData((previous) => ({ ...previous, email: event.target.value }))}
                  placeholder="john.doe@example.com"
                  required
                  type="email"
                  value={formData.email}
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link className="text-sm text-primary" to={ROUTES.forgotPassword}>
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-10 pr-10"
                  disabled={isLoading}
                  id="password"
                  onChange={(event) => setFormData((previous) => ({ ...previous, password: event.target.value }))}
                  placeholder="Enter your password"
                  required
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                />
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  onClick={() => setShowPassword((value) => !value)}
                  type="button"
                >
                  {showPassword ? <EyeOff className="h-4 w-4 text-muted-foreground" /> : <Eye className="h-4 w-4 text-muted-foreground" />}
                </button>
              </div>
            </div>
          </div>

          <Button className="mt-6 w-full gradient-primary" disabled={isLoading} type="submit">
            {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Sign in
          </Button>

          <p className="mt-5 text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link className="font-semibold text-primary" to={ROUTES.register}>
              Sign up
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
