import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Target, ArrowLeft, Sparkles, Loader2, TrendingUp } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { assessmentApi, AssessmentResult } from "@/lib/api";

export default function AssessmentResults() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadResult = async () => {
      if (!assessmentId) {
        setError("No assessment ID provided");
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const data = await assessmentApi.getResult(assessmentId);
        setResult(data);
      } catch (err: any) {
        console.error('Error loading assessment result:', err);

        // Check if result is still processing
        if (err?.response?.status === 202) {
          setError("still_processing");
        } else {
          setError("Could not load assessment results. Please try again.");
        }
      } finally {
        setLoading(false);
      }
    };

    loadResult();
  }, [assessmentId]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mr-3" />
            <span className="text-muted-foreground">Loading results...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error === "still_processing") {
    return (
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              Processing Your Results
            </CardTitle>
            <CardDescription>
              Your assessment is being analyzed. This usually takes just a few seconds.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Our AI is analyzing your responses to provide personalized insights and recommendations.
            </p>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
              >
                Refresh Page
              </Button>
              <Button
                onClick={() => navigate("/dashboard")}
              >
                Go to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Results Not Available</CardTitle>
            <CardDescription>
              {error || "We couldn't find results for this assessment."}
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

  const percentage = Math.min(Math.max(result.overall_score, 0), 100);

  // Determine level based on score
  let level: "Beginner" | "Intermediate" | "Advanced";
  if (percentage < 40) level = "Beginner";
  else if (percentage < 70) level = "Intermediate";
  else level = "Advanced";

  const suggestedDescription =
    level === "Beginner"
      ? `You're at the beginning of your career journey. We recommend starting with core fundamentals and hands-on mini projects to build your confidence.`
      : level === "Intermediate"
      ? `You already have a solid base. Focus on strengthening problem-solving, building portfolio projects, and preparing for real-world interviews.`
      : `You're performing strongly in key skills. It's a great time to specialize, contribute to open-source, mentor others, or target senior-level opportunities.`;

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <Button
            variant="ghost"
            size="sm"
            className="px-0 mb-2 text-muted-foreground hover:text-primary"
            onClick={() => navigate("/assessment")}
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            Back to Assessments
          </Button>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-2">
            <CheckCircle2 className="h-7 w-7 text-primary" />
            Assessment Results
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Here's your personalized analysis and next steps.
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          <Target className="h-3 w-3 mr-1" />
          {result.llm_model_used || 'AI Powered'}
        </Badge>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Overall score */}
        <Card>
          <CardHeader>
            <CardTitle>Overall Score</CardTitle>
            <CardDescription>Your performance on this assessment</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-baseline justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Score</p>
                <p className="text-3xl font-bold">
                  {percentage.toFixed(1)}%
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
              {result.ai_confidence_score && (
                <p className="text-xs text-muted-foreground">
                  AI Confidence: {result.ai_confidence_score.toFixed(0)}%
                </p>
              )}
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
            <CardDescription>Based on your results</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{suggestedDescription}</p>
            {result.ai_insights && (
              <p className="text-sm border-l-2 border-primary pl-3 italic">
                "{result.ai_insights}"
              </p>
            )}
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

      {/* Strengths */}
      {result.strengths.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              Your Strengths
            </CardTitle>
            <CardDescription>Areas where you excel</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.strengths.map((strength, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2 text-sm p-3 rounded-lg border bg-green-50/50 dark:bg-green-900/10"
                >
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Areas for improvement */}
      {result.areas_for_improvement.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Areas for Improvement</CardTitle>
            <CardDescription>Skills to focus on developing</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.areas_for_improvement.map((area, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2 text-sm p-3 rounded-lg border bg-blue-50/50 dark:bg-blue-900/10"
                >
                  <Target className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <span>{area}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Recommended Careers */}
      {result.recommended_careers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recommended Career Paths</CardTitle>
            <CardDescription>Based on your skills and interests</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {result.recommended_careers.map((career, idx) => (
              <div
                key={idx}
                className="flex items-start justify-between gap-4 p-4 rounded-lg border bg-card/50 hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">{career.title}</h3>
                  <p className="text-sm text-muted-foreground">{career.reasoning}</p>
                </div>
                <Badge variant="secondary" className="whitespace-nowrap">
                  {career.match_score}% match
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Top Skills */}
      {result.top_skills && result.top_skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Skills Identified</CardTitle>
            <CardDescription>Your strongest abilities from this assessment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {result.top_skills.map((skill, idx) => (
                <Badge key={idx} variant="outline" className="text-sm">
                  {skill.skill}: {skill.score}%
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3 justify-center pt-4">
        <Button variant="outline" asChild>
          <Link to="/assessment">Take Another Assessment</Link>
        </Button>
        <Button asChild className="gradient-primary">
          <Link to="/dashboard">Go to Dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
