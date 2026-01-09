import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Target, Clock, ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

type QuestionType = "single-choice" | "rating" | "text";

interface Option {
  value: string;
  label: string;
  score: number; // for scoring
}

interface Question {
  id: string;
  type: QuestionType;
  text: string;
  helper?: string;
  category: string;
  options?: Option[]; // for single-choice
  maxRating?: number; // for rating
}

type AnswerMap = Record<string, string>;

const QUESTIONS: Question[] = [
  {
    id: "q1",
    type: "single-choice",
    text: "How familiar are you with programming fundamentals (variables, loops, functions)?",
    helper: "This helps us understand your starting point.",
    category: "Fundamentals",
    options: [
      { value: "none", label: "I’ve never written code before", score: 1 },
      { value: "basic", label: "I’ve done some tutorials / small scripts", score: 2 },
      { value: "comfortable", label: "I can build small apps/projects", score: 4 },
      { value: "advanced", label: "I’m very comfortable and help others learn", score: 5 },
    ],
  },
  {
    id: "q2",
    type: "rating",
    text: "Rate your confidence in problem-solving and debugging.",
    helper: "1 = very low, 5 = very high.",
    category: "Problem Solving",
    maxRating: 5,
  },
  {
    id: "q3",
    type: "rating",
    text: "Rate your familiarity with web technologies (HTML, CSS, JavaScript).",
    category: "Web",
    maxRating: 5,
  },
  {
    id: "q4",
    type: "single-choice",
    text: "Which best describes your current experience level?",
    category: "Experience",
    options: [
      { value: "student", label: "Student / completely new", score: 1 },
      { value: "junior", label: "Junior / < 2 years experience", score: 3 },
      { value: "mid", label: "Mid-level / 2–5 years", score: 4 },
      { value: "senior", label: "Senior / 5+ years", score: 5 },
    ],
  },
  {
    id: "q5",
    type: "text",
    text: "What is your main goal with this career path?",
    helper: "For example: get a first job, switch from another field, grow to senior, freelancing, etc.",
    category: "Goals",
  },
  {
    id: "q6",
    type: "rating",
    text: "How much time per week can you realistically dedicate to learning?",
    helper: "1 = <3 hours, 5 = 15+ hours.",
    category: "Commitment",
    maxRating: 5,
  },
];

export default function AssessmentSession() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [submitting, setSubmitting] = useState(false);

  const selectedPath = searchParams.get("path") || "Selected Career Path";

  const currentQuestion = QUESTIONS[currentIndex];

  const totalQuestions = QUESTIONS.length;
  const answeredCount = useMemo(
    () =>
      QUESTIONS.filter((q) => {
        const val = answers[q.id];
        return val !== undefined && val !== "";
      }).length,
    [answers]
  );

  const progressValue = (answeredCount / totalQuestions) * 100;

  const handleAnswerChange = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const canGoNext = !!answers[currentQuestion.id] || currentQuestion.type === "text";

  const handleNext = () => {
    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const computeScore = () => {
    let totalScore = 0;
    let count = 0;

    for (const q of QUESTIONS) {
      const raw = answers[q.id];
      if (!raw) continue;

      if (q.type === "single-choice" && q.options) {
        const opt = q.options.find((o) => o.value === raw);
        if (opt) {
          totalScore += opt.score;
          count += 1;
        }
      } else if (q.type === "rating" && q.maxRating) {
        const numeric = Number(raw);
        if (!Number.isNaN(numeric)) {
          totalScore += numeric;
          count += 1;
        }
      }
      // text questions are not scored, but still shown in summary
    }

    if (count === 0) return { average: 0, level: "Unknown" as const };

    const average = totalScore / count;

    let level: "Beginner" | "Intermediate" | "Advanced";
    if (average < 2.5) level = "Beginner";
    else if (average < 4) level = "Intermediate";
    else level = "Advanced";

    return { average, level };
  };

  const handleSubmit = () => {
    setSubmitting(true);

    // simple front-end validation: ensure all required questions (non text) are answered
    const missingRequired = QUESTIONS.filter(
      (q) => q.type !== "text" && (!answers[q.id] || answers[q.id].trim() === "")
    );

    if (missingRequired.length > 0) {
      setSubmitting(false);
      toast({
        title: "Incomplete assessment",
        description: "Please answer all required questions before submitting.",
        variant: "destructive",
      });
      return;
    }

    const { average, level } = computeScore();

    // In a real app you'd POST to backend here.
    // For now, we navigate to results with state.
    setTimeout(() => {
      navigate("/assessment/results", {
        state: {
          careerPath: selectedPath,
          score: average,
          level,
          answers,
          questions: QUESTIONS,
        },
      });
      setSubmitting(false);
    }, 600);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl space-y-6">
      {/* Header / Breadcrumb */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Button
              variant="ghost"
              size="sm"
              className="px-0 text-muted-foreground hover:text-primary"
              onClick={() => navigate("/assessment")}
            >
              <ArrowLeft className="mr-1 h-4 w-4" />
              Back to career paths
            </Button>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-2">
            <Target className="h-7 w-7 text-primary" />
            {selectedPath} Assessment
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            One question at a time. This helps us personalize your roadmap and job recommendations.
          </p>
        </div>

        <div className="hidden sm:flex flex-col items-end gap-1">
          <Badge variant="outline" className="text-xs">
            <Clock className="h-3 w-3 mr-1" />
            ~ 5–10 minutes
          </Badge>
          <span className="text-xs text-muted-foreground">
            Question {currentIndex + 1} of {totalQuestions}
          </span>
        </div>
      </div>

      {/* Progress */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center justify-between">
            <span>Assessment Progress</span>
            <span className="text-xs text-muted-foreground">
              {answeredCount} / {totalQuestions} answered
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Progress value={progressValue} className="h-2" />
        </CardContent>
      </Card>

      {/* Question */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Question {currentIndex + 1}: {currentQuestion.text}
          </CardTitle>
          {currentQuestion.helper && (
            <CardDescription>{currentQuestion.helper}</CardDescription>
          )}
          <CardDescription className="mt-1">
            Category: <span className="font-medium text-foreground">{currentQuestion.category}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {currentQuestion.type === "single-choice" && currentQuestion.options && (
            <RadioGroup
              value={answers[currentQuestion.id] || ""}
              onValueChange={(val) => handleAnswerChange(currentQuestion.id, val)}
              className="space-y-3"
            >
              {currentQuestion.options.map((option) => (
                <div
                  key={option.value}
                  className="flex items-center space-x-3 rounded-lg border p-3 hover:bg-muted/50 cursor-pointer"
                >
                  <RadioGroupItem value={option.value} id={option.value} />
                  <Label htmlFor={option.value} className="flex-1 cursor-pointer">
                    {option.label}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          )}

          {currentQuestion.type === "rating" && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Choose a number from 1 (very low) to {currentQuestion.maxRating ?? 5} (very high).
              </p>
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: currentQuestion.maxRating ?? 5 }).map((_, idx) => {
                  const val = String(idx + 1);
                  const isSelected = answers[currentQuestion.id] === val;
                  return (
                    <Button
                      key={val}
                      type="button"
                      variant={isSelected ? "default" : "outline"}
                      className={isSelected ? "gradient-primary" : ""}
                      onClick={() => handleAnswerChange(currentQuestion.id, val)}
                    >
                      {val}
                    </Button>
                  );
                })}
              </div>
            </div>
          )}

          {currentQuestion.type === "text" && (
            <div className="space-y-2">
              <Label htmlFor={currentQuestion.id}>Your answer (optional)</Label>
              <Textarea
                id={currentQuestion.id}
                placeholder="Write your thoughts here..."
                className="min-h-[120px]"
                maxLength={500}
                value={answers[currentQuestion.id] || ""}
                onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                {answers[currentQuestion.id]?.length ?? 0}/500 characters
              </p>
            </div>
          )}

          {/* Navigation buttons */}
          <div className="flex items-center justify-between pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handlePrevious}
              disabled={currentIndex === 0}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Previous
            </Button>

            <div className="flex items-center gap-3">
              {currentIndex < totalQuestions - 1 && (
                <Button
                  type="button"
                  onClick={handleNext}
                  disabled={!canGoNext}
                  className="gradient-primary"
                >
                  Next
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              )}
              {currentIndex === totalQuestions - 1 && (
                <Button
                  type="button"
                  onClick={handleSubmit}
                  disabled={submitting || !canGoNext}
                  className="gradient-primary"
                >
                  {submitting ? (
                    "Submitting..."
                  ) : (
                    <>
                      Submit Assessment
                      <CheckCircle2 className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
