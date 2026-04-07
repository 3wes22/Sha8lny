/**
 * API Client for Sha8lny Backend
 *
 * Provides typed fetch wrapper with authentication handling,
 * error management, and React Query integration helpers.
 */

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Token storage keys
const ACCESS_TOKEN_KEY = 'sha8lny_access_token';
const REFRESH_TOKEN_KEY = 'sha8lny_refresh_token';

// ============================================================================
// Token Management
// ============================================================================

export const tokenStorage = {
  getAccessToken: (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),

  setTokens: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  },

  clearTokens: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  isAuthenticated: (): boolean => !!localStorage.getItem(ACCESS_TOKEN_KEY),
};

// ============================================================================
// API Error Types
// ============================================================================

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data: unknown,
    public url: string
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

export interface ValidationError {
  field: string;
  message: string;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    const extractMessage = (value: unknown): string | null => {
      if (typeof value === "string" && value.trim()) {
        return value;
      }

      if (Array.isArray(value)) {
        for (const item of value) {
          const nested = extractMessage(item);
          if (nested) {
            return nested;
          }
        }
        return null;
      }

      if (value && typeof value === "object") {
        const record = value as Record<string, unknown>;

        const prioritizedKeys = ["details", "detail", "message", "non_field_errors"];
        for (const key of prioritizedKeys) {
          const nested = extractMessage(record[key]);
          if (nested) {
            return nested;
          }
        }

        for (const nestedValue of Object.values(record)) {
          const nested = extractMessage(nestedValue);
          if (nested) {
            return nested;
          }
        }
      }

      return null;
    };

    const message = extractMessage(error.data);
    if (message) {
      return message;
    }

    if (error.status === 401) {
      return "Your session expired. Please sign in again.";
    }
  }

  return fallback;
}

// ============================================================================
// Core API Function
// ============================================================================

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${path}`;
  const token = tokenStorage.getAccessToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle 401 - Token expired, try refresh
  if (response.status === 401 && token) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // Retry original request with new token
      const newToken = tokenStorage.getAccessToken();
      const retryHeaders: HeadersInit = {
        ...headers,
        Authorization: `Bearer ${newToken}`,
      };
      const retryResponse = await fetch(url, { ...options, headers: retryHeaders });

      if (!retryResponse.ok) {
        throw new ApiError(
          retryResponse.status,
          retryResponse.statusText,
          await retryResponse.json().catch(() => null),
          url
        );
      }
      return retryResponse.json() as Promise<T>;
    } else {
      // Refresh failed, clear tokens and redirect to login
      tokenStorage.clearTokens();
      window.location.href = '/login';
      throw new ApiError(401, 'Session expired', null, url);
    }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(response.status, response.statusText, errorData, url);
  }

  // Handle empty responses (204 No Content)
  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

// ============================================================================
// Token Refresh
// ============================================================================

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_URL}/users/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      tokenStorage.setTokens(data.access, data.refresh || refreshToken);
      return true;
    }
  } catch {
    // Refresh failed
  }
  return false;
}

// ============================================================================
// Convenience Methods
// ============================================================================

export const apiClient = {
  get: <T>(path: string, options?: RequestInit) =>
    api<T>(path, { ...options, method: 'GET' }),

  post: <T>(path: string, data?: unknown, options?: RequestInit) =>
    api<T>(path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(path: string, data?: unknown, options?: RequestInit) =>
    api<T>(path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(path: string, data?: unknown, options?: RequestInit) =>
    api<T>(path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(path: string, options?: RequestInit) =>
    api<T>(path, { ...options, method: 'DELETE' }),
};

// ============================================================================
// API Type Definitions (matching Backend models)
// ============================================================================

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  date_of_birth?: string;
  age?: number;
  phone_number?: string;
  is_premium: boolean;
  onboarding_completed: boolean;
  onboarding_step?: number;
  preferred_language: string;
  timezone?: string;
  account_status?: string;
  user_skills?: UserSkill[];
  preferences?: UserPreferences;
  last_login_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// Backend response format: { user, tokens: { access, refresh }, message }
export interface AuthResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
  message: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  username: string;
  full_name: string;
  date_of_birth: string;
  phone_number?: string;
  preferred_language?: 'en' | 'ar';
}

export interface Skill {
  id: string;
  name: string;
  category: string;
  description?: string;
}

export type SkillProficiency = "beginner" | "intermediate" | "advanced" | "expert";

export interface UserSkill {
  id: string;
  skill: Skill;
  proficiency_level: SkillProficiency;
  years_of_experience?: number;
  is_verified: boolean;
}

// Roadmap Template
export interface RoadmapTemplate {
  id: string;
  title: string;
  slug: string;
  description: string;
  short_description: string;
  target_career: string;
  career_level: string;
  estimated_duration_weeks: number;
  difficulty_level: string;
  prerequisites: string[];
  learning_outcomes: string[];
  is_published: boolean;
  usage_count: number;
  created_at: string;
}

// Roadmap Course
export interface RoadmapCourse {
  id: string;
  course: {
    id?: string;
    title?: string;
    provider_name?: string;
    difficulty_level?: string;
    duration_hours?: number;
  };
  order: number;
  is_primary: boolean;
  match_score: string;
  recommendation_reason: string;
  is_enrolled: boolean;
  is_completed: boolean;
  node_type?: "course";
}

export interface RoadmapJourneySummary {
  focus_label: string;
  next_action_title: string;
  next_action_summary: string;
  next_action_type: "phase" | "milestone" | "course" | "roadmap";
  next_action_id?: string;
  completion_ratio: number;
}

export interface RoadmapJourneyNode {
  id: string;
  node_type: "phase" | "milestone" | "course";
  title: string;
  parent_id?: string;
  status: "locked" | "available" | "active" | "completed";
  completion_percentage?: number;
  estimated_effort?: string;
  next_action?: string;
  children?: RoadmapJourneyNode[];
}

export interface RoadmapMilestone {
  id: string;
  title: string;
  description: string;
  milestone_type: 'course' | 'project' | 'reading' | 'practice' | 'assessment';
  order: number;
  estimated_duration_hours: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
  is_required: boolean;
  skills: string[];
  resources: Resource[];
  completed_at?: string;
  courses?: RoadmapCourse[];
  total_courses?: number;
  node_type?: "milestone";
  estimated_effort?: string;
  next_action?: string;
}

// Roadmap Phase
export interface RoadmapPhase {
  id: string;
  title: string;
  description: string;
  order: number;
  estimated_duration_weeks: number;
  status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
  completion_percentage: string;
  started_at?: string;
  completed_at?: string;
  objectives: string[];
  milestones?: RoadmapMilestone[];
  completed_milestones?: number;
  total_milestones?: number;
  node_type?: "phase";
  estimated_effort?: string;
  next_action?: string;
}

// Complete Roadmap
export interface Roadmap {
  id: string;
  template?: string;
  assessment?: string;
  title: string;
  description: string;
  target_career: string;
  current_level: string;
  target_level: string;
  estimated_duration_weeks: number;
  weekly_hours_commitment: number;
  status: 'draft' | 'active' | 'in_progress' | 'completed' | 'paused' | 'archived';
  completion_percentage: string;
  started_at?: string;
  completed_at?: string;
  ai_processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  ai_processed_at?: string;
  ai_insights?: Record<string, unknown> | string;
  llm_model_used?: string;
  llm_prompt_tokens?: number;
  llm_completion_tokens?: number;
  processing_time_seconds?: string;
  metadata?: Record<string, unknown>;
  ai_metadata?: AIInvocationMetadata;
  phases?: RoadmapPhase[];
  total_phases?: number;
  completed_phases?: number;
  is_active?: boolean;
  is_complete?: boolean;
  presentation_mode?: "atlas" | "stacked" | "detail";
  journey_summary?: RoadmapJourneySummary;
  current_focus_node_id?: string;
  journey_nodes?: RoadmapJourneyNode[];
  created_at: string;
  updated_at: string;
}

// Roadmap List Item (minimal info)
export interface RoadmapListItem {
  id: string;
  title: string;
  target_career: string;
  status: string;
  completion_percentage: string;
  estimated_duration_weeks: number;
  ai_processing_status: string;
  created_at: string;
}

// Roadmap Creation Requests
export interface RoadmapCreateFromTemplateRequest {
  template_id: string;
  weekly_hours_commitment?: number;
  customizations?: Record<string, unknown>;
}

export interface RoadmapCreateAIRequest {
  assessment_id?: string;
  target_career?: string;
  current_level?: string;
  target_level?: string;
  weekly_hours_commitment?: number;
}

// Progress Update
export interface RoadmapProgressUpdate {
  phase_id?: string;
  milestone_id?: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
}

export interface Resource {
  title: string;
  url: string;
  type: string;
}

// Job Skill interface
export interface JobSkill {
  id: string;
  skill: string;
  skill_name: string;
  proficiency_level?: string;
  years_required?: number;
  is_required: boolean;
}

// Job Platform interface
export interface JobPlatform {
  id: string;
  name: string;
  slug: string;
  website_url: string;
  logo_url?: string;
  is_active: boolean;
  target_countries: string[];
}

// Job interface (list view - minimal data)
export interface JobListItem {
  id: string;
  title: string;
  company_name: string;
  platform: string;
  platform_name: string;
  location: string;
  location_city: string;
  location_country: string;
  job_type: string;
  experience_level: string;
  salary_min?: string;
  salary_max?: string;
  salary_currency: string;
  is_remote: boolean;
  posted_date: string;
  is_saved?: boolean;
  external_action_available?: boolean;
  skill_match_summary?: string;
}

// Job interface (detail view - full data)
export interface Job {
  id: string;
  platform: JobPlatform;
  title: string;
  company_name: string;
  company_logo_url?: string;
  location: string;
  location_city: string;
  location_country: string;
  remote_type?: string;
  is_remote: boolean;
  job_type: string;
  experience_level: string;
  experience_years_min?: number;
  experience_years_max?: number;
  description: string;
  requirements: string;
  responsibilities: string;
  salary_min?: string;
  salary_max?: string;
  salary_currency: string;
  salary_period?: string;
  salary_disclosed: boolean;
  external_url: string;
  application_deadline?: string;
  posted_date: string;
  skills: JobSkill[];
  is_saved?: boolean;
  external_action_available?: boolean;
  skill_match_summary?: string;
  created_at: string;
}

export interface JobSearchParams {
  query?: string;
  location?: string;
  job_type?: string;
  experience_level?: string;
  skills?: string[];
  is_remote?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  conversation_history?: Array<{ role: 'user' | 'assistant'; content: string }>;
}

export interface AIInvocationMetadata {
  source: 'llm' | 'fallback' | 'baseline';
  processing_time_ms: number;
  model: string | null;
  provider?: string | null;
  version?: string | null;
  trace_id?: string | null;
  fallback_used?: boolean;
  error_code?: string | null;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  delay_ms: number;
  metadata: AIInvocationMetadata;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  id: string;
  email_notifications: boolean;
  push_notifications: boolean;
  weekly_digest: boolean;
  profile_visibility: 'public' | 'private' | 'connections';
  show_progress: boolean;
  preferred_learning_style?: 'visual' | 'auditory' | 'reading' | 'kinesthetic';
  daily_learning_goal_minutes: number;
  reminder_time?: string;
  created_at: string;
  updated_at: string;
}

export interface RoadmapStats {
  total_phases: number;
  completed_phases: number;
  total_milestones: number;
  completed_milestones: number;
  total_courses: number;
  estimated_total_hours: number;
  completion_percentage: number;
  current_focus_node_id?: string;
  next_action?: {
    type: "phase" | "milestone" | "course" | "roadmap";
    id?: string;
    title: string;
    summary: string;
  };
}

export interface SavedJob {
  id: string;
  job: JobListItem;
  notes: string;
  created_at: string;
}

export interface NotificationListItem {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  priority: "low" | "normal" | "high" | "urgent";
  is_read: boolean;
  action_url?: string;
  created_at: string;
  time_ago?: string;
  display_type?: string;
  is_actionable?: boolean;
}

export interface NotificationStats {
  total_count: number;
  unread_count: number;
  urgent_count: number;
  by_type: Record<string, number>;
  recent_notifications: NotificationListItem[];
  nav_summary?: {
    unread_count: number;
    recent_notifications: NotificationListItem[];
  };
}

export interface AssessmentQuestion {
  id: number;
  type: 'multiple_choice' | 'scale' | 'text';
  question: string;
  category: string;
  helper?: string;
  options?: Array<{
    value: string;
    label: string;
    score: number;
  }>;
  min_value?: number;
  max_value?: number;
  labels?: Record<string, string>;
  interaction_mode?: "single_select" | "scale" | "text" | "visual_choice";
  estimated_seconds?: number;
}

export interface AssessmentResponse {
  question_id: number;
  answer: string | number;
  timestamp?: string;
}

export interface Assessment {
  id: string;
  assessment_type: 'skills' | 'career_interests' | 'personality' | 'learning_style' | 'comprehensive';
  target_career?: string;
  questions: AssessmentQuestion[];
  responses: AssessmentResponse[];
  ai_processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  ai_processed_at?: string;
  status: 'draft' | 'in_progress' | 'completed' | 'abandoned';
  started_at?: string;
  completed_at?: string;
  total_questions: number;
  answered_questions: number;
  completion_percentage: number;
  time_spent_seconds: number;
  is_complete: boolean;
  has_result: boolean;
  presentation?: {
    question_count: number;
    current_index: number;
    progress_ratio: number;
    interaction_modes: string[];
    submission_state: "draft" | "submitting" | "processing" | "completed" | "failed";
    result_summary_available: boolean;
    estimated_minutes: number;
  };
  created_at: string;
}

export interface AssessmentCreateRequest {
  assessment_type: 'skills' | 'career_interests' | 'personality' | 'learning_style' | 'comprehensive';
  cv_text?: string;
  career_goals?: string;
  current_skills?: string[];
  target_career?: string;
}

export interface AssessmentSubmitRequest {
  responses: AssessmentResponse[];
}

export interface AssessmentSubmitResponse {
  message: string;
  assessment: Assessment;
  result_id: string;
  submission_state?: "processing" | "completed";
}

export interface AssessmentResult {
  id: string;
  assessment: string;
  overall_score: number;
  skill_scores: Record<string, Record<string, number>>;
  strengths: string[];
  areas_for_improvement: string[];
  recommended_careers: Array<{
    title: string;
    match_score: number;
    reasoning: string;
  }>;
  recommended_learning_paths: Array<{
    skill: string;
    priority: string;
    resources?: string[];
  }>;
  ai_insights: string;
  ai_confidence_score?: number;
  llm_model_used: string;
  llm_prompt_tokens?: number;
  llm_completion_tokens?: number;
  total_tokens_used: number;
  processing_time_seconds?: number;
  ai_metadata?: AIInvocationMetadata;
  top_skills: Array<{
    skill: string;
    score: number;
    category: string;
  }>;
  status_message?: string;
  submission_state?: "processing" | "completed" | "failed";
  next_actions?: Array<{
    label: string;
    route: string;
    kind: "roadmap" | "jobs" | "assessment";
  }>;
  version: string;
  is_shared: boolean;
  created_at: string;
}

export interface AssessmentListItem {
  id: string;
  assessment_type: string;
  status: string;
  completion_percentage: number;
  created_at: string;
}

// ============================================================================
// API Endpoints
// ============================================================================

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<AuthResponse>('/users/auth/login/', data),

  register: (data: RegisterRequest) =>
    apiClient.post<AuthResponse>('/users/auth/register/', data),

  logout: (refresh?: string) =>
    apiClient.post<{ message: string }>('/users/auth/logout/', refresh ? { refresh } : undefined),

  refreshToken: (refresh: string) =>
    apiClient.post<{ access: string; refresh?: string }>('/users/auth/refresh/', { refresh }),
};

export const userApi = {
  getProfile: () =>
    apiClient.get<User>('/users/me/'),

  updateProfile: (data: Partial<User>) =>
    apiClient.patch<User>('/users/me/', data),

  getPreferences: () =>
    apiClient.get<UserPreferences>('/users/me/preferences/'),

  updatePreferences: (data: Partial<UserPreferences>) =>
    apiClient.put<UserPreferences>('/users/me/preferences/', data),

  getSkills: () =>
    apiClient.get<PaginatedResponse<UserSkill>>('/users/user-skills/'),

  addSkill: (skillId: string, proficiency: SkillProficiency) =>
    apiClient.post<UserSkill>('/users/user-skills/', {
      skill_id: skillId,
      proficiency_level: proficiency,
    }),

  removeSkill: (userSkillId: string) =>
    apiClient.delete<void>(`/users/user-skills/${userSkillId}/`),

  getAllSkills: () =>
    apiClient.get<PaginatedResponse<Skill>>('/users/skills/'),
};

// assessmentApi is defined below with complete implementation

export const roadmapApi = {
  // List user's roadmaps
  list: (params?: { status?: string; target_career?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.target_career) searchParams.append('target_career', params.target_career);
    const queryString = searchParams.toString();
    return apiClient.get<PaginatedResponse<RoadmapListItem>>(
      `/roadmap/${queryString ? '?' + queryString : ''}`
    );
  },

  // Get specific roadmap with full hierarchy
  get: (id: string) =>
    apiClient.get<Roadmap>(`/roadmap/${id}/`),

  // Create roadmap from template
  createFromTemplate: (data: RoadmapCreateFromTemplateRequest) =>
    apiClient.post<Roadmap>('/roadmap/', data),

  // Create AI-generated roadmap
  createAI: (data: RoadmapCreateAIRequest) =>
    apiClient.post<Roadmap>('/roadmap/', data),

  // Update roadmap
  update: (id: string, data: Partial<Roadmap>) =>
    apiClient.put<Roadmap>(`/roadmap/${id}/`, data),

  // Delete roadmap
  delete: (id: string) =>
    apiClient.delete<void>(`/roadmap/${id}/`),

  // Update progress (phase or milestone)
  updateProgress: (roadmapId: string, data: RoadmapProgressUpdate) =>
    apiClient.put<{ message: string }>(`/roadmap/${roadmapId}/progress/`, data),

  // Activate roadmap
  activate: (id: string) =>
    apiClient.post<Roadmap>(`/roadmap/${id}/activate/`, {}),

  // Get roadmap statistics
  getStats: (id: string) =>
    apiClient.get<RoadmapStats>(`/roadmap/${id}/stats/`),
};

// Roadmap Template API
export const roadmapTemplateApi = {
  // List all published templates
  list: () =>
    apiClient.get<PaginatedResponse<RoadmapTemplate>>('/roadmap/templates/'),

  // Get specific template
  get: (id: string) =>
    apiClient.get<RoadmapTemplate>(`/roadmap/templates/${id}/`),

  // Filter templates by career
  byCareer: (career: string) =>
    apiClient.get<RoadmapTemplate[]>(`/roadmap/templates/by_career/?career=${encodeURIComponent(career)}`),
};

export const jobApi = {
  // Search jobs with filters
  search: (params: JobSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          // For skills array, join with comma
          if (key === 'skills' && value.length > 0) {
            searchParams.append(key, value.join(','));
          }
        } else {
          searchParams.append(key, String(value));
        }
      }
    });
    return apiClient.get<PaginatedResponse<JobListItem>>(`/jobs/search/?${searchParams.toString()}`);
  },

  // Get all jobs (paginated list)
  list: (params?: { page?: number; page_size?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append('page', String(params.page));
    if (params?.page_size) searchParams.append('page_size', String(params.page_size));
    return apiClient.get<PaginatedResponse<JobListItem>>(`/jobs/?${searchParams.toString()}`);
  },

  // Get job by ID (full details)
  get: (id: string) =>
    apiClient.get<Job>(`/jobs/${id}/`),

  // Save a job
  saveJob: (jobId: string, notes?: string) =>
    apiClient.post<SavedJob>('/jobs/saved-jobs/', {
      job: jobId,
      notes: notes || ''
    }),

  // Unsave a job
  unsaveJob: (savedJobId: string) =>
    apiClient.delete<void>(`/jobs/saved-jobs/${savedJobId}/`),

  // Toggle save status (convenience method)
  toggleSaveJob: (jobId: string) =>
    apiClient.post<{ detail: string; is_saved: boolean; saved_job?: SavedJob }>(`/jobs/saved-jobs/toggle/${jobId}/`, {}),

  // Get all saved jobs
  getSavedJobs: () =>
    apiClient.get<SavedJob[]>('/jobs/saved-jobs/'),
};

export const notificationApi = {
  list: (params?: { unread_only?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.unread_only) {
      searchParams.append("unread_only", "true");
    }

    const queryString = searchParams.toString();
    return apiClient.get<PaginatedResponse<NotificationListItem>>(
      `/notifications/notifications/${queryString ? `?${queryString}` : ""}`,
    );
  },

  getStats: () => apiClient.get<NotificationStats>("/notifications/stats/"),

  markAllRead: () =>
    apiClient.post<{ message: string; count: number }>("/notifications/notifications/mark_all_read/", {}),
};

export const advisorApi = {
  chat: (data: ChatRequest) =>
    apiClient.post<ChatResponse>('/advisory/chat/', data),

  getHistory: () =>
    apiClient.get<Conversation[]>('/advisory/history/'),

  getConversation: (id: string) =>
    apiClient.get<Conversation>(`/advisory/history/${id}/`),
};

export const assessmentApi = {
  list: (params?: { assessment_type?: string; status?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.assessment_type) searchParams.append('assessment_type', params.assessment_type);
    if (params?.status) searchParams.append('status', params.status);
    return apiClient.get<PaginatedResponse<AssessmentListItem>>(`/assessment/?${searchParams.toString()}`);
  },

  get: (id: string) =>
    apiClient.get<Assessment>(`/assessment/${id}/`),

  getLatest: (assessment_type?: string) => {
    const searchParams = new URLSearchParams();
    if (assessment_type) searchParams.append('assessment_type', assessment_type);
    return apiClient.get<Assessment>(`/assessment/latest/?${searchParams.toString()}`);
  },

  create: (data: AssessmentCreateRequest) =>
    apiClient.post<Assessment>('/assessment/', data),

  submit: (id: string, data: AssessmentSubmitRequest) =>
    apiClient.post<AssessmentSubmitResponse>(`/assessment/${id}/submit/`, data),

  getResult: (assessmentId: string) =>
    apiClient.get<AssessmentResult>(`/assessment/${assessmentId}/result/`),

  history: (params?: { assessment_type?: string; status?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.assessment_type) searchParams.append('assessment_type', params.assessment_type);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    return apiClient.get<AssessmentListItem[]>(`/assessment/history/?${searchParams.toString()}`);
  },
};
