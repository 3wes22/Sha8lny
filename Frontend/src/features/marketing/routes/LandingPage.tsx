import { ArrowRight, BriefcaseBusiness, MessageCircleMore, Waypoints } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { PosterHero } from "@/shared/components/PosterHero";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <div className="px-4 py-4 md:px-8">
        <PosterHero
          description="Sha8alny is an AI-powered career atlas for Egyptian learners who need a clearer path from skill signal to roadmap to jobs."
          eyebrow="Sha8alny"
          onPrimaryClick={() => navigate(ROUTES.register)}
          onSecondaryClick={() => navigate(ROUTES.login)}
          primaryLabel="Start your path"
          secondaryLabel="Sign in"
          stats={[
            { label: "Assess", value: "Signal your strengths" },
            { label: "Roadmap", value: "Translate gaps into phases" },
            { label: "Jobs", value: "Move toward real roles" },
          ]}
          title="A career atlas, not another generic dashboard."
          visual={
            <div className="grid gap-4">
              <div className="atlas-panel p-5">
                <div className="flex items-center gap-3">
                  <Waypoints className="h-5 w-5 text-primary" />
                  <p className="text-lg font-semibold">Roadmap as the signature object</p>
                </div>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  View phases, milestones, and next action in one readable operating surface.
                </p>
              </div>
              <div className="atlas-panel p-5">
                <div className="flex items-center gap-3">
                  <MessageCircleMore className="h-5 w-5 text-primary" />
                  <p className="text-lg font-semibold">Advisory for decision support</p>
                </div>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  Use guided assessments and AI advice to keep direction clear.
                </p>
              </div>
              <div className="atlas-panel p-5">
                <div className="flex items-center gap-3">
                  <BriefcaseBusiness className="h-5 w-5 text-primary" />
                  <p className="text-lg font-semibold">Jobs connected to progress</p>
                </div>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  Match opportunity discovery to the skills you already track.
                </p>
              </div>
            </div>
          }
        />
      </div>

      <section className="px-4 pb-10 md:px-8">
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="atlas-panel p-6">
            <p className="type-kicker">1. Diagnose</p>
            <h2 className="mt-3 text-3xl font-bold">Assessment before action</h2>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Start with a professional guided assessment that clarifies strengths, gaps, and likely next steps.
            </p>
          </div>
          <div className="atlas-panel p-6">
            <p className="type-kicker">2. Navigate</p>
            <h2 className="mt-3 text-3xl font-bold">Follow a roadmap that feels spatial</h2>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              See phases, milestones, and progress in a way that keeps the journey readable across desktop and mobile.
            </p>
          </div>
          <div className="atlas-panel p-6">
            <p className="type-kicker">3. Move</p>
            <h2 className="mt-3 text-3xl font-bold">Turn growth into opportunities</h2>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Compare jobs against your current direction, save the right ones, and keep momentum.
            </p>
          </div>
        </div>
        <div className="mt-8 text-center">
          <Button className="gradient-primary" onClick={() => navigate(ROUTES.register)} size="lg">
            Create your account
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </section>
    </div>
  );
}
