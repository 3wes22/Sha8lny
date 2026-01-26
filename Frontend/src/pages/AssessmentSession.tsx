import { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Target, Clock, ArrowLeft, ArrowRight, CheckCircle2, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { assessmentApi, Assessment, AssessmentQuestion, AssessmentResponse } from "@/lib/api";

type AnswerMap = Record<number, string | number>;

export default function AssessmentSession() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [submitting, setSubmitting] = useState(false);

  // Load assessment on mount
  useEffect(() => {
    const loadAssessment = async () => {
      if (!assessmentId) {
        toast({
          title: "Invalid assessment",
          description: "No assessment ID provided",
          variant: "destructive",
        });
        navigate("/assessment");
        return;
      }

      setLoading(true);
      try {
        const data = await assessmentApi.get(assessmentId);
        setAssessment(data);

        // Pre-fill existing responses if any
        if (data.responses && data.responses.length > 0) {
          const existingAnswers: AnswerMap = {};
          data.responses.forEach((r) => {
            existingAnswers[r.question_id] = r.answer;
          });
          setAnswers(existingAnswers);
        }
      } catch (error) {
        console.error('Error loading assessment:', error);
        toast({
          title: "Error loading assessment",
          description: "Could not load the assessment. Please try again.",
          variant: "destructive",
        });
        navigate("/assessment");
      } finally {
        setLoading(false);
      }
    };

    loadAssessment();
  }, [assessmentId, navigate, toast]);

  const questions = assessment?.questions || [];
  const currentQuestion = questions[currentIndex];
  const totalQuestions = questions.length;

  const answeredCount = useMemo(
    () =>
      questions.filter((q) => {
        const val = answers[q.id];
        return val !== undefined && val !== "";
      }).length,
    [questions, answers]
  );

  const progressValue = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;

  const handleAnswerChange = (questionId: number, value: string | number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const canGoNext = currentQuestion
    ? !!answers[currentQuestion.id] || currentQuestion.type === "text"
    : false;

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

  const handleSubmit = async () => {
    if (!assessment || !assessmentId) return;

    setSubmitting(true);

    // Validate all required questions are answered
    const missingRequired = questions.filter(
      (q) => q.type !== "text" && (!answers[q.id] || String(answers[q.id]).trim() === "")
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

    try {
      // Format responses for backend
      const responses: AssessmentResponse[] = questions.map((q) => ({
        question_id: q.id,
        answer: answers[q.id] || "",
        timestamp: new Date().toISOString(),
      }));

      // Submit to backend
      const result = await assessmentApi.submit(assessmentId, { responses });

      toast({
        title: "Assessment submitted!",
        description: "Your results are being processed.",
      });

      // Navigate to results page
      navigate(`/assessment/results/${assessmentId}`);
    } catch (error) {
      console.error('Error submitting assessment:', error);
      toast({
        title: "Error submitting assessment",
        description: "Could not submit your assessment. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mr-3" />
            <span className="text-muted-foreground">Loading assessment...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!assessment || questions.length === 0) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Assessment Not Found</CardTitle>
            <CardDescription>
              The assessment could not be loaded. It may not exist or you may not have permission to access it.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate("/assessment")}>Back to Assessments</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

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
            {assessment.assessment_type.charAt(0).toUpperCase() + assessment.assessment_type.slice(1)} Assessment
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
            Question {currentIndex + 1}: {currentQuestion.question}
          </CardTitle>
          {currentQuestion.helper && (
            <CardDescription>{currentQuestion.helper}</CardDescription>
          )}
          <CardDescription className="mt-1">
            Category: <span className="font-medium text-foreground">{currentQuestion.category}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {currentQuestion.type === "multiple_choice" && currentQuestion.options && (
            <RadioGroup
              value={String(answers[currentQuestion.id] || "")}
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

          {currentQuestion.type === "scale" && (() => {
            // Calculate scale values without useMemo (moved outside hooks context)
            const min = currentQuestion.min_value ?? 1;
            const max = currentQuestion.max_value ?? 5;
            const scaleValues = Array.from({ length: max - min + 1 }, (_, idx) => min + idx);

            return (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Choose a number from {currentQuestion.min_value ?? 1} to {currentQuestion.max_value ?? 5}.
                  {currentQuestion.labels && (
                    <span className="block mt-1">
                      {currentQuestion.labels[String(currentQuestion.min_value ?? 1)]} - {currentQuestion.labels[String(currentQuestion.max_value ?? 5)]}
                    </span>
                  )}
                </p>
                <div className="flex flex-wrap gap-2">
                  {scaleValues.map((val) => {
                    const isSelected = Number(answers[currentQuestion.id]) === val;
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
            );
          })()}

          {currentQuestion.type === "text" && (
            <div className="space-y-2">
              <Label htmlFor={String(currentQuestion.id)}>Your answer (optional)</Label>
              <Textarea
                id={String(currentQuestion.id)}
                placeholder="Write your thoughts here..."
                className="min-h-[120px]"
                maxLength={500}
                value={String(answers[currentQuestion.id] || "")}
                onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                {String(answers[currentQuestion.id] || "").length}/500 characters
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
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
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
