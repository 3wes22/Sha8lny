import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { MainLayout } from "./components/layout/MainLayout";

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

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Index />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes with layout */}
          <Route
            path="/dashboard"
            element={
              <MainLayout>
                <Dashboard />
              </MainLayout>
            }
          />

          <Route
            path="/profile"
            element={
              <MainLayout>
                <Profile />
              </MainLayout>
            }
          />

          <Route
            path="/assessment"
            element={
              <MainLayout>
                <Assessment />
              </MainLayout>
            }
          />
          <Route
            path="/assessment/session"
            element={
              <MainLayout>
                <AssessmentSession />
              </MainLayout>
            }
          />
          <Route
            path="/assessment/results"
            element={
              <MainLayout>
                <AssessmentResults />
              </MainLayout>
            }
          />

          <Route
            path="/roadmap"
            element={
              <MainLayout>
                <Roadmap />
              </MainLayout>
            }
          />
          <Route
            path="/advisor"
            element={
              <MainLayout>
                <Advisor />
              </MainLayout>
            }
          />

          <Route
            path="/jobs"
            element={
              <MainLayout>
                <Jobs />
              </MainLayout>
            }
          />
          <Route
            path="/jobs/saved"
            element={
              <MainLayout>
                <SavedJobs />
              </MainLayout>
            }
          />

          <Route
            path="/settings"
            element={
              <MainLayout>
                <Settings />
              </MainLayout>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
