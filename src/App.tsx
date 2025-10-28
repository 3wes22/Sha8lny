import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import LearningHub from "./pages/LearningHub";
import JobMarketplace from "./pages/JobMarketplace";
import AssessmentCenter from "./pages/AssessmentCenter";
import TakeAssessment from "./pages/TakeAssessment";
import Profile from "./pages/Profile";
import Corporate from "./pages/Corporate";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/learning" element={<LearningHub />} />
          <Route path="/jobs" element={<JobMarketplace />} />
          <Route path="/assessments" element={<AssessmentCenter />} />
          <Route path="/take-assessment" element={<TakeAssessment />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/corporate" element={<Corporate />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
