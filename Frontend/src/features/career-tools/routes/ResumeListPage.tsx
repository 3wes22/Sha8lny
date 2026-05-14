import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { resumeApi, type ResumeListItem, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { ResumeCard } from "@/features/career-tools/components/ResumeCard";
import { toast } from "sonner";

export default function ResumeListPage() {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await resumeApi.list();
        // Handle both paginated and flat array responses
        setResumes(Array.isArray(data) ? data : (data as { results?: ResumeListItem[] }).results ?? []);
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to load resumes"));
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <PageShell
      actions={
        <Link to="/career-tools/resumes/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Resume
          </Button>
        </Link>
      }
      description="Create, manage, and optimize your resumes for ATS systems."
      eyebrow="Career Tools"
      title="Resume Builder"
    >
      {resumes.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {resumes.map((resume) => (
            <ResumeCard key={resume.id} resume={resume} />
          ))}
        </div>
      ) : (
        <StatePanel
          description="Create your first resume to get started with ATS-optimized applications."
          state="empty"
          title="No resumes yet"
          action={
            <Link to="/career-tools/resumes/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Resume
              </Button>
            </Link>
          }
        />
      )}
    </PageShell>
  );
}
