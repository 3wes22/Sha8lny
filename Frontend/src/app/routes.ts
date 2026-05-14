import type { LucideIcon } from "lucide-react";
import {
  Bell,
  BookMarked,
  BriefcaseBusiness,
  FileText,
  LayoutDashboard,
  MessageCircleMore,
  Settings,
  Target,
  UserRound,
  Waypoints,
} from "lucide-react";

export const ROUTES = {
  home: "/",
  login: "/login",
  register: "/register",
  forgotPassword: "/forgot-password",
  dashboard: "/dashboard",
  profile: "/profile",
  assessment: "/assessment",
  assessmentSession: (assessmentId = ":assessmentId") => `/assessment/session/${assessmentId}`,
  assessmentResults: (assessmentId = ":assessmentId") => `/assessment/results/${assessmentId}`,
  roadmap: "/roadmap",
  advisor: "/advisor",
  jobs: "/jobs",
  savedJobs: "/jobs/saved",
  jobDetail: (jobId = ":jobId") => `/jobs/${jobId}`,
  settings: "/settings",
  notifications: "/notifications",
  resumeList: "/career-tools/resumes",
  resumeNew: "/career-tools/resumes/new",
  resumeEdit: (resumeId = ":resumeId") => `/career-tools/resumes/${resumeId}/edit`,
  resumePreview: (resumeId = ":resumeId") => `/career-tools/resumes/${resumeId}`,
} as const;

export interface AppRouteMeta {
  key: string;
  path: string;
  title: string;
  description: string;
  protected: boolean;
  showInPrimaryNav?: boolean;
  icon?: LucideIcon;
}

export const APP_ROUTE_META: AppRouteMeta[] = [
  {
    key: "home",
    path: ROUTES.home,
    title: "Career Atlas",
    description: "Poster-like landing surface for Sha8alny.",
    protected: false,
  },
  {
    key: "login",
    path: ROUTES.login,
    title: "Sign In",
    description: "Return to your roadmap, jobs, and assessments.",
    protected: false,
  },
  {
    key: "register",
    path: ROUTES.register,
    title: "Create Account",
    description: "Start a guided career-growth setup.",
    protected: false,
  },
  {
    key: "forgotPassword",
    path: ROUTES.forgotPassword,
    title: "Recover Access",
    description: "Request the next password recovery step.",
    protected: false,
  },
  {
    key: "dashboard",
    path: ROUTES.dashboard,
    title: "Dashboard",
    description: "See your current position, pace, and next move.",
    protected: true,
    showInPrimaryNav: true,
    icon: LayoutDashboard,
  },
  {
    key: "assessment",
    path: ROUTES.assessment,
    title: "Assessment",
    description: "Launch and manage skill-readiness assessments.",
    protected: true,
    showInPrimaryNav: true,
    icon: Target,
  },
  {
    key: "roadmap",
    path: ROUTES.roadmap,
    title: "Roadmap",
    description: "Navigate your phase, milestone, and course journey.",
    protected: true,
    showInPrimaryNav: true,
    icon: Waypoints,
  },
  {
    key: "advisor",
    path: ROUTES.advisor,
    title: "Advisory",
    description: "Ask for guidance and next-step clarity.",
    protected: true,
    showInPrimaryNav: true,
    icon: MessageCircleMore,
  },
  {
    key: "jobs",
    path: ROUTES.jobs,
    title: "Jobs",
    description: "Search roles that fit your current direction.",
    protected: true,
    showInPrimaryNav: true,
    icon: BriefcaseBusiness,
  },
  {
    key: "savedJobs",
    path: ROUTES.savedJobs,
    title: "Saved Jobs",
    description: "Revisit bookmarked job opportunities.",
    protected: true,
    showInPrimaryNav: true,
    icon: BookMarked,
  },
  {
    key: "notifications",
    path: ROUTES.notifications,
    title: "Notifications",
    description: "Review alerts across learning and job activity.",
    protected: true,
    icon: Bell,
  },
  {
    key: "profile",
    path: ROUTES.profile,
    title: "Profile",
    description: "Update identity, language, and skill signals.",
    protected: true,
    icon: UserRound,
  },
  {
    key: "settings",
    path: ROUTES.settings,
    title: "Settings",
    description: "Adjust delivery, privacy, and reminder preferences.",
    protected: true,
    icon: Settings,
  },
  {
    key: "resumeList",
    path: ROUTES.resumeList,
    title: "Resume Builder",
    description: "Build and optimize your professional resume.",
    protected: true,
    showInPrimaryNav: true,
    icon: FileText,
  },
  {
    key: "jobDetail",
    path: ROUTES.jobDetail(),
    title: "Job Detail",
    description: "Inspect one job opportunity in depth.",
    protected: true,
  },
  {
    key: "assessmentSession",
    path: ROUTES.assessmentSession(),
    title: "Assessment Session",
    description: "Continue the active assessment flow.",
    protected: true,
  },
  {
    key: "assessmentResults",
    path: ROUTES.assessmentResults(),
    title: "Assessment Results",
    description: "Read processed assessment outcomes and next steps.",
    protected: true,
  },
];

export const PRIMARY_NAV_ITEMS = APP_ROUTE_META.filter((route) => route.showInPrimaryNav);

export const APP_ROUTE_PATTERNS = APP_ROUTE_META.map((route) => route.path);

const normalisePath = (path: string) => path.replace(/\/+$/, "") || "/";

const matchPattern = (pathname: string, pattern: string) => {
  const current = normalisePath(pathname).split("/");
  const target = normalisePath(pattern).split("/");

  if (current.length !== target.length) {
    return false;
  }

  return target.every((segment, index) => segment.startsWith(":") || segment === current[index]);
};

export const getRouteMeta = (pathname: string) =>
  APP_ROUTE_META.find((route) => matchPattern(pathname, route.path))
  ?? APP_ROUTE_META.find((route) => route.path === ROUTES.dashboard)
  ?? APP_ROUTE_META[0];
