import { useState } from "react";
import { Loader2, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AssessmentIntroHero } from "@/features/assessment/components/AssessmentIntroHero";
import { assessmentApi } from "@/lib/api";
import { ChoiceCard } from "@/shared/components/ChoiceCard";
import { PageShell } from "@/shared/components/PageShell";
import { SectionHeader } from "@/shared/components/SectionHeader";
import { StatePanel } from "@/shared/components/StatePanel";
import { useToast } from "@/hooks/use-toast";

const careerPaths = [
  ["Software Engineer", "Build and ship product software."],
  ["Frontend Developer", "Focus on responsive, high-quality interfaces."],
  ["Backend Developer", "Design APIs, services, and platform logic."],
  ["Data Scientist", "Work with analysis, models, and experimentation."],
  ["Product Manager", "Lead direction, discovery, and delivery."],
  ["UI/UX Designer", "Shape flows, interfaces, and usability systems."],
];

export default function AssessmentPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [creatingAssessment, setCreatingAssessment] = useState(false);

  const filteredPaths = careerPaths.filter(
    ([title, description]) =>
      title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      description.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const handleStartAssessment = async (careerPath: string) => {
    setCreatingAssessment(true);
    try {
      const assessment = await assessmentApi.create({
        assessment_type: "skills",
        target_career: careerPath,
      });
      navigate(`/assessment/session/${assessment.id}`);
    } catch {
      toast({
        title: "Error creating assessment",
        description: "Could not start the assessment. Please try again.",
        variant: "destructive",
      });
    } finally {
      setCreatingAssessment(false);
    }
  };

  return (
    <PageShell
      description="Choose a path and start the guided evaluation."
      eyebrow="Assessment"
      title="Skill assessment"
    >
      <AssessmentIntroHero />

      <section className="space-y-4">
        <SectionHeader
          action={
            <Button
              disabled={creatingAssessment}
              onClick={() => handleStartAssessment("Custom Career Path")}
              variant="outline"
            >
              {creatingAssessment ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Custom path
            </Button>
          }
          description="Use a role that matches your target direction. The assessment content stays serious and professional, not quiz-game playful."
          title="Choose a career track"
        />

        <div className="atlas-panel p-5">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-10"
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search for a path..."
              value={searchQuery}
            />
          </div>
        </div>

        {filteredPaths.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredPaths.map(([title, description]) => (
              <ChoiceCard
                description={description}
                disabled={creatingAssessment}
                key={title}
                onClick={() => handleStartAssessment(title)}
                title={title}
              />
            ))}
          </div>
        ) : (
          <StatePanel
            description="Try another search term or create a custom path."
            state="empty"
            title="No paths match this search"
          />
        )}
      </section>
    </PageShell>
  );
}
