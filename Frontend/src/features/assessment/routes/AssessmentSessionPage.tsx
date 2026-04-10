import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { AssessmentProgressRail } from "@/features/assessment/components/AssessmentProgressRail";
import { AssessmentQuestionCard } from "@/features/assessment/components/AssessmentQuestionCard";
import { ChoiceReveal } from "@/features/assessment/components/ChoiceReveal";
import { assessmentApi, type Assessment, type AssessmentResponse } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { useToast } from "@/hooks/use-toast";

type AnswerMap = Record<number, string | number>;

export default function AssessmentSessionPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [waitingForQuestions, setWaitingForQuestions] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let ignore = false;
    let pollTimer: ReturnType<typeof setTimeout> | null = null;

    const loadAssessment = async () => {
      if (!assessmentId) {
        navigate("/assessment");
        return;
      }

      try {
        setLoading(true);
        const data = await assessmentApi.get(assessmentId);
        if (ignore) {
          return;
        }

        setAssessment(data);

        const existingAnswers: AnswerMap = {};
        data.responses?.forEach((response) => {
          existingAnswers[response.question_id] = response.answer;
        });
        setAnswers(existingAnswers);

        const questionGenerationPending =
          data.questions.length === 0 &&
          (data.ai_processing_status === "pending" || data.ai_processing_status === "processing");

        setWaitingForQuestions(questionGenerationPending);

        if (questionGenerationPending) {
          pollTimer = setTimeout(() => void loadAssessment(), 2000);
        }
      } catch {
        if (!ignore) {
          toast({
            title: "Error loading assessment",
            description: "Could not load the assessment. Please try again.",
            variant: "destructive",
          });
          navigate("/assessment");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    void loadAssessment();

    return () => {
      ignore = true;
      if (pollTimer) {
        clearTimeout(pollTimer);
      }
    };
  }, [assessmentId, navigate, toast]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!assessment || assessment.questions.length === 0) {
    if (waitingForQuestions || assessment?.presentation?.submission_state === "generating") {
      return (
        <StatePanel
          description="We are generating the questions for this assessment. Stay on this screen and it will become ready automatically."
          state="processing"
          title="Preparing assessment"
        />
      );
    }

    return (
      <StatePanel
        description="The assessment could not be loaded."
        state="error"
        title="Assessment unavailable"
      />
    );
  }

  const currentQuestion = assessment.questions[currentIndex];
  const answeredCount = assessment.questions.filter((question) => {
    const value = answers[question.id];
    return value !== undefined && value !== "";
  }).length;

  const handleSubmit = async () => {
    if (!assessmentId) return;

    const missingRequired = assessment.questions.filter(
      (question) => question.type !== "text" && (answers[question.id] === undefined || answers[question.id] === ""),
    );
    if (missingRequired.length > 0) {
      toast({
        title: "Incomplete assessment",
        description: "Please answer the required questions before submitting.",
        variant: "destructive",
      });
      return;
    }

    try {
      setSubmitting(true);
      const responses: AssessmentResponse[] = assessment.questions.map((question) => ({
        question_id: question.id,
        answer: answers[question.id] ?? "",
        timestamp: new Date().toISOString(),
      }));

      await assessmentApi.submit(assessmentId, { responses });
      navigate(`/assessment/results/${assessmentId}`);
    } catch {
      toast({
        title: "Error submitting assessment",
        description: "Could not submit your answers. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageShell
      actions={
        <Button onClick={() => navigate("/assessment")} variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to paths
        </Button>
      }
      description="Move question by question. Each choice should feel deliberate and readable."
      eyebrow="Assessment session"
      title={`${assessment.assessment_type.replace("_", " ")} assessment`}
      aside={
        <div className="space-y-4">
          <AssessmentProgressRail
            answeredCount={answeredCount}
            assessment={assessment}
            currentIndex={currentIndex}
          />
          <ChoiceReveal value={answers[currentQuestion.id]} />
        </div>
      }
    >
      <AssessmentQuestionCard
        onChange={(value) => setAnswers((previous) => ({ ...previous, [currentQuestion.id]: value }))}
        question={currentQuestion}
        value={answers[currentQuestion.id]}
      />

      <div className="flex flex-wrap justify-between gap-3">
        <Button
          disabled={currentIndex === 0}
          onClick={() => setCurrentIndex((index) => Math.max(0, index - 1))}
          variant="outline"
        >
          Previous
        </Button>
        <div className="flex gap-3">
          {currentIndex < assessment.questions.length - 1 ? (
            <Button onClick={() => setCurrentIndex((index) => index + 1)}>
              Next
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button className="gradient-primary" disabled={submitting} onClick={handleSubmit}>
              {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Submit assessment
            </Button>
          )}
        </div>
      </div>
    </PageShell>
  );
}
