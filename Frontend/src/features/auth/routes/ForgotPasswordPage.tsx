import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-screen px-4 py-6 md:px-8">
      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="poster-surface overflow-hidden rounded-[2rem] border border-border/70 px-6 py-8 md:px-10">
          <p className="type-kicker">Recovery</p>
          <h1 className="mt-4 text-balance text-5xl font-bold md:text-7xl">Account recovery is not wired yet.</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Password reset is out of scope for the graduation MVP. Use your existing credentials or contact an
            administrator if you are locked out of a demo account.
          </p>
        </section>

        <div className="atlas-panel p-6 md:p-8">
          <Link className="inline-flex items-center gap-2 text-sm text-muted-foreground" to={ROUTES.login}>
            <ArrowLeft className="h-4 w-4" />
            Back to sign in
          </Link>
          <div className="mt-5 space-y-2">
            <p className="type-kicker">Reset password</p>
            <h2 className="text-4xl font-bold">Not available in MVP</h2>
          </div>

          <div className="mt-6 rounded-[1.5rem] border border-amber-500/30 bg-amber-500/5 p-5 text-sm text-muted-foreground">
            <p className="font-semibold text-foreground">Backend endpoint not implemented</p>
            <p className="mt-2">
              There is no `/users/auth/password-reset/` flow in the current API. This page is kept as a route stub so
              the login link does not 404, but no email is sent from here.
            </p>
          </div>

          <Button asChild className="gradient-primary mt-6 w-full">
            <Link to={ROUTES.login}>Return to sign in</Link>
          </Button>
        </div>
      </div>
    </div>
  );
};
