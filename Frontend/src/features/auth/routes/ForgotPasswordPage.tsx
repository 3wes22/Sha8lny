import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className="min-h-screen px-4 py-6 md:px-8">
      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="poster-surface overflow-hidden rounded-[2rem] border border-border/70 px-6 py-8 md:px-10">
          <p className="type-kicker">Recovery</p>
          <h1 className="mt-4 text-balance text-5xl font-bold md:text-7xl">Recover access without losing your place.</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            The account recovery flow can plug into the backend later. For now, keep the next step clear and low-friction.
          </p>
        </section>

        <div className="atlas-panel p-6 md:p-8">
          <Link className="inline-flex items-center gap-2 text-sm text-muted-foreground" to={ROUTES.login}>
            <ArrowLeft className="h-4 w-4" />
            Back to sign in
          </Link>
          <div className="mt-5 space-y-2">
            <p className="type-kicker">Reset password</p>
            <h2 className="text-4xl font-bold">Recover access</h2>
          </div>

          {submitted ? (
            <div className="mt-6 rounded-[1.5rem] border border-primary/20 bg-primary/5 p-5 text-sm text-muted-foreground">
              If an account exists for <span className="font-semibold text-foreground">{email}</span>, the recovery instructions can be connected here.
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="reset-email">Email</Label>
                <Input
                  id="reset-email"
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  type="email"
                  value={email}
                />
              </div>
              <Button className="gradient-primary w-full" disabled={!email.trim()} onClick={() => setSubmitted(true)}>
                Continue
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
