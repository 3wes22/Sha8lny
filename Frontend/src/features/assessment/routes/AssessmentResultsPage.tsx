import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useParams } from "react-router-dom";

import { ApiError, assessmentApi, type AssessmentResult, getApiErrorMessage } from "@/lib/api";
import { AssessmentOutcomeCards } from "@/features/assessment/components/AssessmentOutcomeCards";
import { AssessmentResultHero } from "@/features/assessment/components/AssessmentResultHero";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";

export default function AssessmentResultsPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    let pollTimer: ReturnType<typeof setTimeout> | null = null;

    const loadResult = async () => {
      if (!assessmentId) {
        setError("No assessment ID provided.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await assessmentApi.getResult(assessmentId);
        if (!ignore) {
          setResult(data);
          setProcessing(false);
          setError(null);
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 202) {
          if (!ignore) {
            setProcessing(true);
            setError(null);
            pollTimer = setTimeout(() => void loadResult(), 3000);
          }
        } else if (!ignore) {
          setError(getApiErrorMessage(err, "Could not load assessment results."));
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    void loadResult();

    return () => {
      ignore = true;
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [assessmentId]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (processing) {
    return (
      <StatePanel
        description="The backend is still processing your answers. Stay on this screen and the result will appear automatically."
        state="processing"
        title="Processing assessment"
      />
    );
  }

  if (error || !result) {
    return (
      <StatePanel
        description={error ?? "We couldn't find the result for this assessment."}
        state="error"
        title="Results unavailable"
      />
    );
  }

  return (
    <PageShell
      description="Use this result to decide whether to continue through the roadmap or jump into job exploration."
      eyebrow="Assessment results"
      title="Outcome ready"
    >
      <AssessmentResultHero result={result} />
      <AssessmentOutcomeCards result={result} />
    </PageShell>
  );
}
