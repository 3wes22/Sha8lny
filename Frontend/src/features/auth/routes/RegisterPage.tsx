import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/context/AuthContext";
import { useToast } from "@/hooks/use-toast";

export default function RegisterPage() {
  const { toast } = useToast();
  const { register, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    username: "",
    full_name: "",
    email: "",
    password: "",
    password_confirm: "",
    date_of_birth: "",
  });

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (formData.password !== formData.password_confirm) {
      toast({
        title: "Passwords do not match",
        description: "Please check the password confirmation.",
        variant: "destructive",
      });
      return;
    }

    try {
      await register(formData);
    } catch {
      // handled in context
    }
  };

  return (
    <div className="min-h-screen px-4 py-6 md:px-8">
      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="poster-surface overflow-hidden rounded-[2rem] border border-border/70 px-6 py-8 md:px-10">
          <p className="type-kicker">Create account</p>
          <h1 className="mt-4 text-balance text-5xl font-bold md:text-7xl">Start with a clearer direction.</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Sha8alny is for students, job seekers, and professionals who want a path that connects assessment, roadmap, advisory, and jobs.
          </p>
        </section>

        <form className="atlas-panel p-6 md:p-8" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <p className="type-kicker">Account setup</p>
            <h2 className="text-4xl font-bold">Sign up</h2>
            <p className="text-sm text-muted-foreground">Create your account to start the guided flow.</p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input id="username" onChange={(event) => setFormData((previous) => ({ ...previous, username: event.target.value }))} value={formData.username} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="full_name">Full name</Label>
              <Input id="full_name" onChange={(event) => setFormData((previous) => ({ ...previous, full_name: event.target.value }))} value={formData.full_name} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" onChange={(event) => setFormData((previous) => ({ ...previous, email: event.target.value }))} type="email" value={formData.email} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" onChange={(event) => setFormData((previous) => ({ ...previous, password: event.target.value }))} type="password" value={formData.password} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password_confirm">Confirm password</Label>
              <Input id="password_confirm" onChange={(event) => setFormData((previous) => ({ ...previous, password_confirm: event.target.value }))} type="password" value={formData.password_confirm} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="date_of_birth">Date of birth</Label>
              <Input id="date_of_birth" onChange={(event) => setFormData((previous) => ({ ...previous, date_of_birth: event.target.value }))} type="date" value={formData.date_of_birth} />
            </div>
          </div>

          <Button className="mt-6 w-full gradient-primary" disabled={isLoading} type="submit">
            {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Create account
          </Button>

          <p className="mt-5 text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link className="font-semibold text-primary" to={ROUTES.login}>
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
