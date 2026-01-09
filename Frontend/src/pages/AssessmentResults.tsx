import { useLocation, useNavigate, Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Target, ArrowLeft, Sparkles } from "lucide-react";

type QuestionType = "single-choice" | "rating" | "text";

interface Question {
  id: string;
  type: QuestionType;
  text: string;
  helper?: string;
  category: string;
  options?: { value: string; label: string; score: number }[];
  maxRating?: number;
}

interface AssessmentResultState {
  careerPath: string;
  score: number;
  level: "Beginner" | "Intermediate" | "Advanced" | "Unknown";
  answers: Record<string, string>;
  questions: Question[];
}

export default function AssessmentResults() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as Partial<AssessmentResultState>;

  if (!state.questions || !state.answers) {
    // No state: user refreshed or came here directly
    return (
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Assessment Results</CardTitle>
            <CardDescription>
              We couldn&apos;t find any recent assessment results. Please take an assessment first.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between gap-4">
            <Button variant="outline" asChild>
              <Link to="/assessment">Back to Assessments</Link>
            </Button>
            <Button className="gradient-primary" asChild>
              <Link to="/assessment">Start a New Assessment</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { careerPath, score, level, questions, answers } = state;

  const normalizedScore = Math.min(Math.max(score ?? 0, 0), 5);
  const percentage = (normalizedScore / 5) * 100;

  const suggestedTitle =
    level === "Beginner"
      ? `Foundations for ${careerPath}`
      : level === "Intermediate"
      ? `${careerPath} Growth Plan`
      : `${careerPath} Advanced Roadmap`;

  const suggestedDescription =
    level === "Beginner"
      ? `You’re at the beginning of your ${careerPath} journey. We recommend starting with core fundamentals and hands-on mini projects to build your confidence.`
      : level === "Intermediate"
      ? `You already have a solid base for ${careerPath}. Focus on strengthening problem-solving, building portfolio projects, and preparing for real-world interviews.`
      : `You’re performing strongly in key skills for ${careerPath}. It’s a great time to specialize, contribute to open-source, mentor others, or target senior-level opportunities.`;

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <Button
            variant="ghost"
            size="sm"
            className="px-0 mb-2 text-muted-foreground hover:text-primary"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-2">
            <CheckCircle2 className="h-7 w-7 text-primary" />
            Assessment Results
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Here&apos;s a summary of your answers and a suggested direction for your next steps.
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          <Target className="h-3 w-3 mr-1" />
          {careerPath}
        </Badge>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Overall score */}
        <Card>
          <CardHeader>
            <CardTitle>Overall Readiness</CardTitle>
            <CardDescription>Your current fit for this career path</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-baseline justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Average score</p>
                <p className="text-3xl font-bold">
                  {normalizedScore.toFixed(1)} <span className="text-base text-muted-foreground">/ 5</span>
                </p>
              </div>
              <Badge
                className={
                  level === "Beginner"
                    ? "bg-orange-100 text-orange-800 border-orange-200"
                    : level === "Intermediate"
                    ? "bg-blue-100 text-blue-800 border-blue-200"
                    : "bg-emerald-100 text-emerald-800 border-emerald-200"
                }
              >
                {level}
              </Badge>
            </div>
            <div className="space-y-2">
              <Progress value={percentage} className="h-2" />
              <p className="text-xs text-muted-foreground">
                This score is based on your self-rated skills and experience. Use it as a guide, not a label.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Suggested path */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Suggested Next Step
            </CardTitle>
            <CardDescription>{suggestedTitle}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{suggestedDescription}</p>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">Personalized Roadmap</Badge>
              <Badge variant="secondary">Skill Gaps</Badge>
              <Badge variant="secondary">Recommended Jobs</Badge>
            </div>
            <div className="flex flex-wrap gap-3 pt-2">
              <Button asChild className="gradient-primary">
                <Link to="/roadmap">View Learning Roadmap</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link to="/jobs">Explore Job Matches</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Answers summary */}
      <Card>
        <CardHeader>
          <CardTitle>Summary of Your Answers</CardTitle>
          <CardDescription>
            You can use this to reflect on where you feel strong and where you’d like to grow.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {questions.map((q) => {
            const rawAnswer = answers[q.id];
            let displayAnswer = rawAnswer ?? "Not answered";

            if (q.type === "single-choice" && q.options) {
              const found = q.options.find((o) => o.value === rawAnswer);
              if (found) displayAnswer = found.label;
            }

            if (q.type === "rating") {
              displayAnswer = rawAnswer ? `${rawAnswer} / ${q.maxRating ?? 5}` : "Not rated";
            }

            return (
              <div
                key={q.id}
                className="rounded-lg border p-4 flex flex-col gap-2 bg-card/40"
              >
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium">{q.text}</p>
                    <p className="text-xs text-muted-foreground">
                      Category: {q.category} • Type: {q.type === "rating" ? "Rating" : q.type === "text" ? "Open" : "Multiple choice"}
                    </p>
                  </div>
                </div>
                <div className="mt-1">
                  <p className="text-sm">
                    <span className="text-xs uppercase tracking-wide text-muted-foreground mr-1">
                      Your answer:
                    </span>
                    <span className="font-medium">{displayAnswer}</span>
                  </p>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
