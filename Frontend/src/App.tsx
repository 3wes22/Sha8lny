import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { MainLayout } from "./components/layout/MainLayout";
import { AuthProvider, ProtectedRoute } from "./contexts/AuthContext";

import Index from "./pages/Index";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import Assessment from "./pages/Assessment";
import AssessmentSession from "./pages/AssessmentSession";
import AssessmentResults from "./pages/AssessmentResults";
import Jobs from "./pages/Jobs";
import SavedJobs from "./pages/SavedJobs";
import Advisor from "./pages/Advisor";
import Roadmap from "./pages/Roadmap";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<Index />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes with layout */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Dashboard />
                  </MainLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Profile />
                  </MainLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/assessment"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Assessment />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/assessment/session/:assessmentId"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <AssessmentSession />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/assessment/results/:assessmentId"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <AssessmentResults />
                  </MainLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/roadmap"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Roadmap />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/advisor"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Advisor />
                  </MainLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/jobs"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Jobs />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/jobs/saved"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <SavedJobs />
                  </MainLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Settings />
                  </MainLayout>
                </ProtectedRoute>
              }
            />

            {/* Catch-all */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
