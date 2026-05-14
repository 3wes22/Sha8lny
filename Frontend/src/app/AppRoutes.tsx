import { lazy, Suspense, type ReactElement } from "react";
import { Loader2 } from "lucide-react";
import { Route, Routes } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import NotFoundPage from "@/app/NotFoundPage";
import { ProtectedRoute } from "@/features/auth/context/AuthContext";
import { MainLayout } from "@/shared/layout/MainLayout";

const LandingPage = lazy(() => import("@/features/marketing/routes/LandingPage"));
const LoginPage = lazy(() => import("@/features/auth/routes/LoginPage"));
const RegisterPage = lazy(() => import("@/features/auth/routes/RegisterPage"));
const ForgotPasswordPage = lazy(() => import("@/features/auth/routes/ForgotPasswordPage"));
const DashboardPage = lazy(() => import("@/features/dashboard/routes/DashboardPage"));
const AssessmentPage = lazy(() => import("@/features/assessment/routes/AssessmentPage"));
const AssessmentSessionPage = lazy(() => import("@/features/assessment/routes/AssessmentSessionPage"));
const AssessmentResultsPage = lazy(() => import("@/features/assessment/routes/AssessmentResultsPage"));
const RoadmapPage = lazy(() => import("@/features/roadmap/routes/RoadmapPage"));
const AdvisoryPage = lazy(() => import("@/features/advisory/routes/AdvisoryPage"));
const JobsPage = lazy(() => import("@/features/jobs/routes/JobsPage"));
const SavedJobsPage = lazy(() => import("@/features/jobs/routes/SavedJobsPage"));
const JobDetailPage = lazy(() => import("@/features/jobs/routes/JobDetailPage"));
const NotificationsPage = lazy(() => import("@/features/notifications/routes/NotificationsPage"));
const ProfilePage = lazy(() => import("@/features/profile/routes/ProfilePage"));
const SettingsPage = lazy(() => import("@/features/settings/routes/SettingsPage"));
const ResumeListPage = lazy(() => import("@/features/career-tools/routes/ResumeListPage"));
const ResumeEditorPage = lazy(() => import("@/features/career-tools/routes/ResumeEditorPage"));
const ResumePreviewPage = lazy(() => import("@/features/career-tools/routes/ResumePreviewPage"));

const withProtectedLayout = (element: ReactElement) => (
  <ProtectedRoute>
    <MainLayout>{element}</MainLayout>
  </ProtectedRoute>
);

export const AppRoutes = () => {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <Routes>
        <Route path={ROUTES.home} element={<LandingPage />} />
        <Route path={ROUTES.login} element={<LoginPage />} />
        <Route path={ROUTES.register} element={<RegisterPage />} />
        <Route path={ROUTES.forgotPassword} element={<ForgotPasswordPage />} />

        <Route path={ROUTES.dashboard} element={withProtectedLayout(<DashboardPage />)} />
        <Route path={ROUTES.profile} element={withProtectedLayout(<ProfilePage />)} />
        <Route path={ROUTES.assessment} element={withProtectedLayout(<AssessmentPage />)} />
        <Route
          path={ROUTES.assessmentSession()}
          element={withProtectedLayout(<AssessmentSessionPage />)}
        />
        <Route
          path={ROUTES.assessmentResults()}
          element={withProtectedLayout(<AssessmentResultsPage />)}
        />
        <Route path={ROUTES.roadmap} element={withProtectedLayout(<RoadmapPage />)} />
        <Route path={ROUTES.advisor} element={withProtectedLayout(<AdvisoryPage />)} />
        <Route path={ROUTES.jobs} element={withProtectedLayout(<JobsPage />)} />
        <Route path={ROUTES.savedJobs} element={withProtectedLayout(<SavedJobsPage />)} />
        <Route path={ROUTES.jobDetail()} element={withProtectedLayout(<JobDetailPage />)} />
        <Route
          path={ROUTES.notifications}
          element={withProtectedLayout(<NotificationsPage />)}
        />
        <Route path={ROUTES.resumeList} element={withProtectedLayout(<ResumeListPage />)} />
        <Route path={ROUTES.resumeNew} element={withProtectedLayout(<ResumeEditorPage />)} />
        <Route path={ROUTES.resumeEdit()} element={withProtectedLayout(<ResumeEditorPage />)} />
        <Route path={ROUTES.resumePreview()} element={withProtectedLayout(<ResumePreviewPage />)} />
        <Route path={ROUTES.settings} element={withProtectedLayout(<SettingsPage />)} />

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
};
