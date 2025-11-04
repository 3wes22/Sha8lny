# SkillPath AI - Database Schema Design

> **Document Version:** 1.0
> **Last Updated:** November 4, 2025
> **Database:** PostgreSQL 15+

---

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [Core Tables](#core-tables)
3. [Entity Relationship Diagram](#entity-relationship-diagram)
4. [Indexing Strategy](#indexing-strategy)
5. [Migration Strategy](#migration-strategy)
6. [Sample Queries](#sample-queries)

---

## Schema Overview

### Design Principles

1. **Normalization:** 3NF (Third Normal Form) for data integrity
2. **Performance:** Strategic denormalization where justified
3. **Scalability:** Support for horizontal partitioning (future)
4. **Audit Trail:** `created_at` and `updated_at` on all tables
5. **Soft Deletes:** `deleted_at` for recoverable records

### Database Naming Conventions

- **Tables:** `snake_case`, plural (e.g., `users`, `assessment_sessions`)
- **Columns:** `snake_case` (e.g., `user_id`, `created_at`)
- **Primary Keys:** `id` (UUID or BIGSERIAL)
- **Foreign Keys:** `{table_name}_id` (e.g., `user_id`, `assessment_id`)
- **Indexes:** `idx_{table}_{columns}` (e.g., `idx_users_email`)

---

## Core Tables

### 1. Users & Authentication

#### **users**
Primary table for all registered users.

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    email_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

**Roles:** `admin`, `user`, `moderator` (future)

---

#### **user_profiles**
Extended user information.

```sql
CREATE TABLE user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    bio TEXT,
    location VARCHAR(255),
    avatar_url VARCHAR(500),
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    education_level VARCHAR(100),
    years_of_experience INTEGER,
    current_job_title VARCHAR(255),
    profile_completion_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_location ON user_profiles(location);
```

---

#### **user_preferences**
User settings and preferences.

```sql
CREATE TABLE user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_type VARCHAR(50) NOT NULL DEFAULT 'learner', -- 'learner' or 'jobseeker'
    career_goals TEXT[],
    target_skills TEXT[],
    learning_pace VARCHAR(50) DEFAULT 'moderate', -- 'slow', 'moderate', 'fast'
    notification_email BOOLEAN DEFAULT TRUE,
    notification_in_app BOOLEAN DEFAULT TRUE,
    notification_frequency VARCHAR(50) DEFAULT 'daily', -- 'instant', 'daily', 'weekly'
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'Africa/Cairo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
```

---

#### **refresh_tokens**
JWT refresh token storage.

```sql
CREATE TABLE refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    device_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

---

#### **verification_tokens**
Email verification, password reset tokens.

```sql
CREATE TABLE verification_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'email_verification', 'password_reset'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_verification_tokens_token ON verification_tokens(token);
CREATE INDEX idx_verification_tokens_user_type ON verification_tokens(user_id, type);
```

---

### 2. Skills System

#### **skills**
Master skill catalog.

```sql
CREATE TABLE skills (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL, -- 'programming', 'design', 'marketing', etc.
    description TEXT,
    icon_url VARCHAR(500),
    parent_skill_id BIGINT REFERENCES skills(id), -- For skill hierarchy
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_skills_slug ON skills(slug);
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_parent ON skills(parent_skill_id);
```

---

#### **user_skills**
User skill proficiency tracking.

```sql
CREATE TABLE user_skills (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id BIGINT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    proficiency_level VARCHAR(50) NOT NULL, -- 'beginner', 'intermediate', 'advanced', 'expert'
    proficiency_score INTEGER, -- 0-100
    source VARCHAR(50), -- 'assessment', 'self_reported', 'course_completion'
    verified BOOLEAN DEFAULT FALSE,
    acquired_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, skill_id)
);

-- Indexes
CREATE INDEX idx_user_skills_user_id ON user_skills(user_id);
CREATE INDEX idx_user_skills_skill_id ON user_skills(skill_id);
CREATE INDEX idx_user_skills_proficiency ON user_skills(proficiency_level);
```

---

### 3. Assessment System

#### **assessments**
Assessment definitions.

```sql
CREATE TABLE assessments (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    skill_id BIGINT REFERENCES skills(id),
    difficulty VARCHAR(50) NOT NULL DEFAULT 'medium', -- 'easy', 'medium', 'hard'
    question_count INTEGER NOT NULL,
    time_limit_minutes INTEGER, -- NULL = no time limit
    passing_score INTEGER DEFAULT 70,
    is_adaptive BOOLEAN DEFAULT TRUE,
    is_published BOOLEAN DEFAULT FALSE,
    tags TEXT[],
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_assessments_slug ON assessments(slug);
CREATE INDEX idx_assessments_skill_id ON assessments(skill_id);
CREATE INDEX idx_assessments_difficulty ON assessments(difficulty);
CREATE INDEX idx_assessments_published ON assessments(is_published);
```

---

#### **questions**
Question bank.

```sql
CREATE TABLE questions (
    id BIGSERIAL PRIMARY KEY,
    assessment_id BIGINT REFERENCES assessments(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'mcq', 'true_false', 'code_completion', 'short_answer', 'coding_challenge'
    difficulty VARCHAR(50) NOT NULL DEFAULT 'medium',
    question_text TEXT NOT NULL,
    question_data JSONB, -- Flexible field for question-specific data
    options JSONB, -- For MCQ: [{"id": "a", "text": "Option A"}, ...]
    correct_answer JSONB, -- Varies by question type
    explanation TEXT,
    points INTEGER DEFAULT 1,
    time_estimate_seconds INTEGER,
    skill_tags TEXT[],
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_questions_assessment_id ON questions(assessment_id);
CREATE INDEX idx_questions_type ON questions(type);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_skill_tags ON questions USING GIN(skill_tags);
```

**Example `question_data` for different types:**

```json
// MCQ
{
  "question": "What is 2 + 2?",
  "options": [
    {"id": "a", "text": "3"},
    {"id": "b", "text": "4"},
    {"id": "c", "text": "5"}
  ],
  "correct_answer": "b"
}

// Code Completion
{
  "question": "Complete the function to reverse a string",
  "code_template": "function reverseString(str) {\n  // Your code here\n}",
  "test_cases": [
    {"input": "hello", "expected": "olleh"},
    {"input": "world", "expected": "dlrow"}
  ]
}

// Coding Challenge
{
  "question": "Implement a function that finds the longest palindrome in a string",
  "starter_code": "function longestPalindrome(s) {\n  \n}",
  "test_cases": [...],
  "time_limit_ms": 3000,
  "memory_limit_mb": 256
}
```

---

#### **assessment_sessions**
User assessment attempts.

```sql
CREATE TABLE assessment_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_id BIGINT NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress', -- 'in_progress', 'paused', 'completed', 'abandoned'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    paused_at TIMESTAMP WITH TIME ZONE,
    total_time_seconds INTEGER DEFAULT 0,
    current_question_index INTEGER DEFAULT 0,
    score INTEGER,
    percentage NUMERIC(5,2),
    passed BOOLEAN,
    session_data JSONB, -- For adaptive logic state
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_assessment_sessions_user_id ON assessment_sessions(user_id);
CREATE INDEX idx_assessment_sessions_assessment_id ON assessment_sessions(assessment_id);
CREATE INDEX idx_assessment_sessions_status ON assessment_sessions(status);
CREATE INDEX idx_assessment_sessions_completed_at ON assessment_sessions(completed_at DESC);
```

---

#### **user_answers**
Individual question answers.

```sql
CREATE TABLE user_answers (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    question_id BIGINT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    user_answer JSONB NOT NULL,
    is_correct BOOLEAN,
    points_earned INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,
    ai_evaluation JSONB, -- For open-ended questions evaluated by AI
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, question_id)
);

-- Indexes
CREATE INDEX idx_user_answers_session_id ON user_answers(session_id);
CREATE INDEX idx_user_answers_question_id ON user_answers(question_id);
CREATE INDEX idx_user_answers_is_correct ON user_answers(is_correct);
```

---

#### **assessment_results**
Aggregated assessment results.

```sql
CREATE TABLE assessment_results (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT UNIQUE NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_id BIGINT NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    max_score INTEGER NOT NULL,
    percentage NUMERIC(5,2) NOT NULL,
    time_taken_seconds INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    skill_breakdown JSONB, -- {"javascript": 85, "react": 70, ...}
    skill_gaps TEXT[],
    strengths TEXT[],
    recommendations TEXT[],
    certificate_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_assessment_results_user_id ON assessment_results(user_id);
CREATE INDEX idx_assessment_results_assessment_id ON assessment_results(assessment_id);
CREATE INDEX idx_assessment_results_passed ON assessment_results(passed);
CREATE INDEX idx_assessment_results_created_at ON assessment_results(created_at DESC);
```

---

### 4. Learning Paths & Courses

#### **roadmaps**
Personalized learning roadmaps.

```sql
CREATE TABLE roadmaps (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_result_id BIGINT REFERENCES assessment_results(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_skill_id BIGINT REFERENCES skills(id),
    estimated_duration_days INTEGER,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'archived'
    progress_percentage INTEGER DEFAULT 0,
    generated_by VARCHAR(50) DEFAULT 'ai', -- 'ai', 'manual', 'template'
    generation_data JSONB, -- AI prompt and parameters used
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_roadmaps_user_id ON roadmaps(user_id);
CREATE INDEX idx_roadmaps_target_skill ON roadmaps(target_skill_id);
CREATE INDEX idx_roadmaps_status ON roadmaps(status);
```

---

#### **roadmap_items**
Individual steps in a roadmap.

```sql
CREATE TABLE roadmap_items (
    id BIGSERIAL PRIMARY KEY,
    roadmap_id BIGINT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    skill_id BIGINT REFERENCES skills(id),
    item_type VARCHAR(50) NOT NULL, -- 'course', 'project', 'practice', 'reading'
    resource_id BIGINT, -- Links to courses, projects, etc.
    estimated_hours INTEGER,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'skipped'
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_roadmap_items_roadmap_id ON roadmap_items(roadmap_id);
CREATE INDEX idx_roadmap_items_sequence ON roadmap_items(roadmap_id, sequence_order);
CREATE INDEX idx_roadmap_items_status ON roadmap_items(status);
```

---

#### **courses**
Learning resource catalog.

```sql
CREATE TABLE courses (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    provider VARCHAR(100), -- 'Coursera', 'Udemy', 'YouTube', 'Internal'
    external_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    difficulty_level VARCHAR(50),
    duration_hours INTEGER,
    language VARCHAR(10) DEFAULT 'en',
    price_egp NUMERIC(10,2) DEFAULT 0,
    skill_tags TEXT[],
    rating NUMERIC(3,2),
    enrollment_count INTEGER DEFAULT 0,
    is_free BOOLEAN DEFAULT TRUE,
    is_published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_courses_slug ON courses(slug);
CREATE INDEX idx_courses_provider ON courses(provider);
CREATE INDEX idx_courses_skill_tags ON courses USING GIN(skill_tags);
CREATE INDEX idx_courses_difficulty ON courses(difficulty_level);
CREATE INDEX idx_courses_is_free ON courses(is_free);
```

---

#### **user_course_enrollments**
User course enrollment tracking.

```sql
CREATE TABLE user_course_enrollments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    roadmap_item_id BIGINT REFERENCES roadmap_items(id),
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    progress_percentage INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'enrolled', -- 'enrolled', 'in_progress', 'completed', 'dropped'
    completed_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    time_spent_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, course_id)
);

-- Indexes
CREATE INDEX idx_enrollments_user_id ON user_course_enrollments(user_id);
CREATE INDEX idx_enrollments_course_id ON user_course_enrollments(course_id);
CREATE INDEX idx_enrollments_status ON user_course_enrollments(status);
```

---

### 5. Job Marketplace

#### **jobs**
Job listing aggregation.

```sql
CREATE TABLE jobs (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE, -- ID from source platform
    title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    company_logo_url VARCHAR(500),
    description TEXT NOT NULL,
    requirements TEXT,
    location VARCHAR(255),
    employment_type VARCHAR(50), -- 'full_time', 'part_time', 'contract', 'internship'
    experience_level VARCHAR(50), -- 'entry', 'mid', 'senior'
    salary_min NUMERIC(12,2),
    salary_max NUMERIC(12,2),
    currency VARCHAR(10) DEFAULT 'EGP',
    required_skills TEXT[],
    nice_to_have_skills TEXT[],
    source VARCHAR(100) NOT NULL, -- 'LinkedIn', 'Wuzzuf', 'Bayt', 'Manual'
    external_url VARCHAR(500) NOT NULL,
    posted_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0,
    application_count INTEGER DEFAULT 0,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_jobs_external_id ON jobs(external_id);
CREATE INDEX idx_jobs_company ON jobs(company_name);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_employment_type ON jobs(employment_type);
CREATE INDEX idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX idx_jobs_required_skills ON jobs USING GIN(required_skills);
CREATE INDEX idx_jobs_posted_at ON jobs(posted_at DESC);
CREATE INDEX idx_jobs_is_active ON jobs(is_active);
CREATE INDEX idx_jobs_source ON jobs(source);
```

---

#### **saved_jobs**
User job bookmarks.

```sql
CREATE TABLE saved_jobs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    notes TEXT,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id)
);

-- Indexes
CREATE INDEX idx_saved_jobs_user_id ON saved_jobs(user_id);
CREATE INDEX idx_saved_jobs_job_id ON saved_jobs(job_id);
```

---

#### **job_applications** (Future)
Track user applications.

```sql
CREATE TABLE job_applications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'applied', -- 'applied', 'viewed', 'interviewing', 'offered', 'rejected'
    cover_letter TEXT,
    resume_url VARCHAR(500),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id)
);

-- Indexes
CREATE INDEX idx_job_applications_user_id ON job_applications(user_id);
CREATE INDEX idx_job_applications_job_id ON job_applications(job_id);
CREATE INDEX idx_job_applications_status ON job_applications(status);
```

---

#### **job_matches**
Precalculated user-job compatibility scores.

```sql
CREATE TABLE job_matches (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    match_score INTEGER NOT NULL, -- 0-100
    matching_skills TEXT[],
    missing_skills TEXT[],
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id)
);

-- Indexes
CREATE INDEX idx_job_matches_user_score ON job_matches(user_id, match_score DESC);
CREATE INDEX idx_job_matches_job_id ON job_matches(job_id);
```

---

### 6. Notifications & Engagement

#### **notifications**
User notifications.

```sql
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'assessment_reminder', 'roadmap_ready', 'job_match', etc.
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    action_url VARCHAR(500),
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high'
    read_at TIMESTAMP WITH TIME ZONE,
    sent_via_email BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_notifications_user_read ON notifications(user_id, read_at);
CREATE INDEX idx_notifications_user_created ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_type ON notifications(type);
```

---

#### **user_activity_log**
Track user actions for engagement analytics.

```sql
CREATE TABLE user_activity_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL, -- 'login', 'assessment_started', 'course_viewed', etc.
    activity_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_activity_log_user_id ON user_activity_log(user_id, created_at DESC);
CREATE INDEX idx_activity_log_type ON user_activity_log(activity_type);
CREATE INDEX idx_activity_log_created_at ON user_activity_log(created_at DESC);
```

---

### 7. Analytics & Admin

#### **ai_usage_tracking**
Track AI API usage and costs.

```sql
CREATE TABLE ai_usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    service_type VARCHAR(50) NOT NULL, -- 'question_generation', 'answer_evaluation', 'roadmap_generation'
    model_name VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    estimated_cost_usd NUMERIC(10,6),
    request_data JSONB,
    response_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_ai_usage_user_id ON ai_usage_tracking(user_id);
CREATE INDEX idx_ai_usage_service_type ON ai_usage_tracking(service_type);
CREATE INDEX idx_ai_usage_created_at ON ai_usage_tracking(created_at DESC);
```

---

#### **admin_actions**
Audit trail for admin operations.

```sql
CREATE TABLE admin_actions (
    id BIGSERIAL PRIMARY KEY,
    admin_user_id BIGINT NOT NULL REFERENCES users(id),
    action_type VARCHAR(100) NOT NULL, -- 'user_banned', 'assessment_published', etc.
    target_type VARCHAR(100), -- 'user', 'assessment', 'course', etc.
    target_id BIGINT,
    action_data JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_admin_actions_admin_user ON admin_actions(admin_user_id);
CREATE INDEX idx_admin_actions_target ON admin_actions(target_type, target_id);
CREATE INDEX idx_admin_actions_created_at ON admin_actions(created_at DESC);
```

---

## Entity Relationship Diagram

```
┌─────────────┐
│    users    │
└──────┬──────┘
       │
       ├──────────────────────────────┬────────────────────────┐
       │                              │                        │
       ▼                              ▼                        ▼
┌──────────────┐            ┌──────────────────┐      ┌──────────────┐
│user_profiles │            │user_preferences  │      │refresh_tokens│
└──────────────┘            └──────────────────┘      └──────────────┘
       │
       │
       ├──────────────────┬────────────────────┬─────────────────┐
       │                  │                    │                 │
       ▼                  ▼                    ▼                 ▼
┌──────────────┐   ┌─────────────────┐  ┌──────────────┐  ┌──────────┐
│ user_skills  │   │assessment_      │  │  roadmaps    │  │saved_jobs│
│              │   │  sessions       │  │              │  │          │
└──────────────┘   └─────────────────┘  └──────────────┘  └──────────┘
       │                   │                    │                │
       │                   │                    │                │
       ▼                   ▼                    ▼                ▼
┌──────────────┐   ┌─────────────────┐  ┌──────────────┐  ┌──────────┐
│   skills     │   │ user_answers    │  │roadmap_items │  │   jobs   │
│              │   │                 │  │              │  │          │
└──────────────┘   └─────────────────┘  └──────────────┘  └──────────┘
       │                   │                    │
       │                   │                    │
       ▼                   ▼                    ▼
┌──────────────┐   ┌─────────────────┐  ┌──────────────┐
│ assessments  │   │assessment_      │  │   courses    │
│              │   │  results        │  │              │
└──────────────┘   └─────────────────┘  └──────────────┘
       │                                        │
       │                                        │
       ▼                                        ▼
┌──────────────┐                      ┌─────────────────┐
│  questions   │                      │user_course_     │
│              │                      │  enrollments    │
└──────────────┘                      └─────────────────┘
```

---

## Indexing Strategy

### Performance-Critical Indexes

#### User Lookup
```sql
-- Email login (most frequent query)
CREATE INDEX idx_users_email ON users(email);

-- User authentication state
CREATE INDEX idx_users_active_verified ON users(is_active, email_verified);
```

#### Assessment Queries
```sql
-- Find user's assessment sessions
CREATE INDEX idx_assessment_sessions_user_status ON assessment_sessions(user_id, status);

-- Assessment analytics
CREATE INDEX idx_assessment_results_assessment_date ON assessment_results(assessment_id, created_at DESC);

-- Question retrieval for adaptive testing
CREATE INDEX idx_questions_assessment_difficulty ON questions(assessment_id, difficulty);
```

#### Job Search
```sql
-- Job search with filters
CREATE INDEX idx_jobs_active_posted ON jobs(is_active, posted_at DESC) WHERE is_active = TRUE;

-- Skill-based job search
CREATE INDEX idx_jobs_skills_gin ON jobs USING GIN(required_skills);

-- Location-based search
CREATE INDEX idx_jobs_location_trgm ON jobs USING gin(location gin_trgm_ops);
```

#### Roadmap & Learning
```sql
-- User's active roadmaps
CREATE INDEX idx_roadmaps_user_status ON roadmaps(user_id, status);

-- Course recommendations by skill
CREATE INDEX idx_courses_skill_rating ON courses USING GIN(skill_tags);
```

---

### Full-Text Search Indexes

```sql
-- Enable pg_trgm extension for fuzzy search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Job title and description search
CREATE INDEX idx_jobs_title_trgm ON jobs USING gin(title gin_trgm_ops);
CREATE INDEX idx_jobs_description_trgm ON jobs USING gin(description gin_trgm_ops);

-- Course search
CREATE INDEX idx_courses_title_trgm ON courses USING gin(title gin_trgm_ops);
```

---

## Migration Strategy

### Initial Migration (MVP)

**Order of table creation:**
1. Core tables: `users`, `user_profiles`, `user_preferences`
2. Auth tables: `refresh_tokens`, `verification_tokens`
3. Skills: `skills`, `user_skills`
4. Assessments: `assessments`, `questions`, `assessment_sessions`, `user_answers`, `assessment_results`
5. Learning: `roadmaps`, `roadmap_items`, `courses`, `user_course_enrollments`
6. Jobs: `jobs`, `saved_jobs`, `job_matches`
7. Engagement: `notifications`, `user_activity_log`
8. Admin: `ai_usage_tracking`, `admin_actions`

### Migration Tools

**TypeORM Migration Example:**
```typescript
import { MigrationInterface, QueryRunner } from "typeorm";

export class CreateUsersTable1699000000000 implements MigrationInterface {
    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`
            CREATE TABLE users (
                id BIGSERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'user',
                email_verified BOOLEAN DEFAULT FALSE,
                last_login_at TIMESTAMP WITH TIME ZONE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP WITH TIME ZONE
            );

            CREATE INDEX idx_users_email ON users(email);
            CREATE INDEX idx_users_role ON users(role);
        `);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`DROP TABLE users CASCADE;`);
    }
}
```

---

## Sample Queries

### User Authentication
```sql
-- Register user
INSERT INTO users (email, password_hash, role)
VALUES ('user@example.com', '$2b$12$...', 'user')
RETURNING id, email, role;

-- Login query
SELECT id, email, password_hash, role, is_active, email_verified
FROM users
WHERE email = 'user@example.com' AND is_active = TRUE;

-- Get user profile
SELECT u.*, up.*, upr.*
FROM users u
LEFT JOIN user_profiles up ON u.id = up.user_id
LEFT JOIN user_preferences upr ON u.id = upr.user_id
WHERE u.id = 123;
```

---

### Assessment Flow
```sql
-- Start assessment session
INSERT INTO assessment_sessions (user_id, assessment_id, status)
VALUES (123, 456, 'in_progress')
RETURNING id, started_at;

-- Get next question (adaptive)
SELECT q.*
FROM questions q
WHERE q.assessment_id = 456
  AND q.difficulty = 'medium'
  AND q.id NOT IN (
    SELECT question_id FROM user_answers WHERE session_id = 789
  )
ORDER BY RANDOM()
LIMIT 1;

-- Submit answer
INSERT INTO user_answers (session_id, question_id, user_answer, is_correct, time_taken_seconds)
VALUES (789, 101, '{"answer": "b"}', TRUE, 45);

-- Calculate final score
SELECT
    COUNT(*) as total_questions,
    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_answers,
    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as percentage
FROM user_answers
WHERE session_id = 789;
```

---

### Personalized Roadmap
```sql
-- Generate roadmap from assessment
INSERT INTO roadmaps (user_id, assessment_result_id, title, description)
VALUES (123, 456, 'Web Development Roadmap', 'Personalized path based on assessment')
RETURNING id;

-- Add roadmap items
INSERT INTO roadmap_items (roadmap_id, sequence_order, title, skill_id, item_type, estimated_hours)
VALUES
    (789, 1, 'Learn JavaScript Basics', 10, 'course', 20),
    (789, 2, 'Build a Todo App', 10, 'project', 10),
    (789, 3, 'Master React Fundamentals', 15, 'course', 30);

-- Get user's active roadmap with progress
SELECT
    r.*,
    COUNT(ri.id) as total_items,
    SUM(CASE WHEN ri.status = 'completed' THEN 1 ELSE 0 END) as completed_items
FROM roadmaps r
LEFT JOIN roadmap_items ri ON r.id = ri.roadmap_id
WHERE r.user_id = 123 AND r.status = 'active'
GROUP BY r.id;
```

---

### Job Matching
```sql
-- Find matching jobs for user
SELECT
    j.*,
    jm.match_score,
    jm.matching_skills,
    jm.missing_skills
FROM jobs j
INNER JOIN job_matches jm ON j.id = jm.job_id
WHERE jm.user_id = 123
  AND j.is_active = TRUE
  AND jm.match_score >= 70
ORDER BY jm.match_score DESC, j.posted_at DESC
LIMIT 20;

-- Calculate job match score (batch processing)
WITH user_skills_cte AS (
    SELECT skill_id, proficiency_score
    FROM user_skills
    WHERE user_id = 123
)
INSERT INTO job_matches (user_id, job_id, match_score, matching_skills, missing_skills)
SELECT
    123,
    j.id,
    calculate_match_score(j.required_skills, array_agg(s.name)) as match_score,
    array_agg(s.name) FILTER (WHERE s.name = ANY(j.required_skills)) as matching_skills,
    array_difference(j.required_skills, array_agg(s.name)) as missing_skills
FROM jobs j
CROSS JOIN user_skills_cte us
LEFT JOIN skills s ON us.skill_id = s.id
WHERE j.is_active = TRUE
GROUP BY j.id
ON CONFLICT (user_id, job_id) DO UPDATE
SET match_score = EXCLUDED.match_score,
    matching_skills = EXCLUDED.matching_skills,
    missing_skills = EXCLUDED.missing_skills,
    calculated_at = CURRENT_TIMESTAMP;
```

---

### Analytics Queries
```sql
-- User engagement metrics
SELECT
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_activities
FROM user_activity_log
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Assessment performance metrics
SELECT
    a.title,
    COUNT(ar.id) as attempts,
    AVG(ar.percentage) as avg_score,
    AVG(ar.time_taken_seconds) as avg_time,
    SUM(CASE WHEN ar.passed THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as pass_rate
FROM assessments a
LEFT JOIN assessment_results ar ON a.id = ar.assessment_id
WHERE ar.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.id, a.title
ORDER BY attempts DESC;

-- AI cost tracking
SELECT
    DATE(created_at) as date,
    service_type,
    SUM(total_tokens) as total_tokens,
    SUM(estimated_cost_usd) as total_cost_usd
FROM ai_usage_tracking
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at), service_type
ORDER BY date DESC, service_type;
```

---

## Database Maintenance

### Backup Strategy
```bash
# Daily automated backup
pg_dump -U skillpath_user -d skillpath_db -F c -f backup_$(date +%Y%m%d).dump

# Backup with compression
pg_dump -U skillpath_user -d skillpath_db -F c -Z 9 -f backup_$(date +%Y%m%d).dump
```

### Cleanup Jobs
```sql
-- Delete expired refresh tokens (daily)
DELETE FROM refresh_tokens
WHERE expires_at < CURRENT_TIMESTAMP;

-- Delete old verification tokens (weekly)
DELETE FROM verification_tokens
WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Archive old activity logs (monthly)
-- Move to separate archive table or cold storage
```

### Performance Monitoring
```sql
-- Find slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

---

**Database Schema Document Prepared By:** SkillPath AI Development Team
**Version:** 1.0 (MVP)
**Next Review:** After initial implementation feedback
