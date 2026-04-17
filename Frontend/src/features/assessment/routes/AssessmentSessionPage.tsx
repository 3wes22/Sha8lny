import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { AnalyzingTransition } from "@/features/assessment/components/AnalyzingTransition";
import { AssessmentProgressRail } from "@/features/assessment/components/AssessmentProgressRail";
import { AssessmentQuestionCard } from "@/features/assessment/components/AssessmentQuestionCard";
import { ChoiceReveal } from "@/features/assessment/components/ChoiceReveal";
import { assessmentApi, type Assessment, type AssessmentQuestion, type AssessmentResponse } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { useToast } from "@/hooks/use-toast";

type AnswerMap = Record<string, string | number>;

function getActiveQuestions(assessment: Assessment | null): AssessmentQuestion[] {
  if (!assessment) {
    return [];
  }
  if (assessment.active_questions?.length) {
    return assessment.active_questions;
  }
  return assessment.questions ?? [];
}

export default function AssessmentSessionPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [submitting, setSubmitting] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let ignore = false;

    const loadAssessment = async () => {
      if (!assessmentId) {
        navigate("/assessment");
        return;
      }

      try {
        if (!assessment) {
          setLoading(true);
        }

        const data = await assessmentApi.get(assessmentId);
        if (ignore) {
          return;
        }

        setAssessment(data);
        setCurrentIndex(0);

        const existingAnswers: AnswerMap = {};
        data.responses?.forEach((response) => {
          existingAnswers[String(response.question_id)] = response.answer;
        });
        setAnswers(existingAnswers);
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
    };
  }, [assessmentId, navigate, refreshTick, toast]);

  const activeQuestions = getActiveQuestions(assessment);
  const submissionState = assessment?.presentation?.submission_state;
  const analyzingStage =
    submissionState === "stage_1_analyzing"
      ? "stage_1"
      : submissionState === "stage_2_analyzing"
      ? "stage_2"
        : null;

  useEffect(() => {
    if (
      submissionState !== "stage_1_generating" &&
      submissionState !== "stage_1_analyzing" &&
      submissionState !== "stage_2_analyzing"
    ) {
      return;
    }

    const pollTimer = setTimeout(() => {
      setRefreshTick((value) => value + 1);
    }, 2000);

    return () => {
      clearTimeout(pollTimer);
    };
  }, [submissionState]);

  if (loading && !assessment) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!assessment) {
    return (
      <StatePanel
        description="The assessment could not be loaded."
        state="error"
        title="Assessment unavailable"
      />
    );
  }

  if (submissionState === "stage_1_generating") {
    return (
      <StatePanel
        description="We are generating the first stage of questions. Stay on this screen and it will become ready automatically."
        state="processing"
        title="Preparing assessment"
      />
    );
  }

  if (analyzingStage) {
    return (
      <PageShell
        description="The assessment is moving to the next processing step."
        eyebrow="Assessment session"
        title="Assessment in progress"
      >
        <AnalyzingTransition stage={analyzingStage} />
      </PageShell>
    );
  }

  if (activeQuestions.length === 0) {
    return (
      <StatePanel
        description="The assessment could not be loaded."
        state="error"
        title="Assessment unavailable"
      />
    );
  }

  const currentQuestion = activeQuestions[currentIndex];
  const answeredCount = activeQuestions.filter((question) => {
    const value = answers[String(question.id)];
    return value !== undefined && value !== "";
  }).length;

  const handleSubmit = async () => {
    if (!assessmentId) return;

    const missingRequired = activeQuestions.filter(
      (question) =>
        question.type !== "text" &&
        (answers[String(question.id)] === undefined || answers[String(question.id)] === ""),
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
      const responses: AssessmentResponse[] = activeQuestions.map((question) => ({
        question_id: question.id,
        answer: answers[String(question.id)] ?? "",
        timestamp: new Date().toISOString(),
      }));

      const response = await assessmentApi.submit(assessmentId, { responses });

      if (assessment.stage === "stage_1") {
        setAssessment(response.assessment);
        setAnswers({});
        setCurrentIndex(0);
        return;
      }

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
            assessment={{ ...assessment, questions: activeQuestions }}
            currentIndex={currentIndex}
          />
          <ChoiceReveal value={answers[String(currentQuestion.id)]} />
        </div>
      }
    >
      <AssessmentQuestionCard
        onChange={(value) => setAnswers((previous) => ({ ...previous, [String(currentQuestion.id)]: value }))}
        question={currentQuestion}
        value={answers[String(currentQuestion.id)]}
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
          {currentIndex < activeQuestions.length - 1 ? (
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
