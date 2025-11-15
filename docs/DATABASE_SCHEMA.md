# Sha8alny - Database Schema

## Overview
This document defines the complete PostgreSQL database schema for the Sha8alny platform. The schema follows microservices principles with logical separation by service domain while maintaining data integrity through foreign key relationships where necessary.

**Database:** PostgreSQL (Latest Stable Version)  
**Design Principles:**
- Normalized structure (3NF minimum)
- Clear table naming conventions
- Comprehensive indexing for performance
- Soft deletes where applicable
- Audit fields (created_at, updated_at) on all tables
- UUID primary keys for distributed system readiness

---

## Schema Organization by Service

### Services and Their Tables
1. **User Service**: users, user_skills, skills, user_preferences
2. **Assessment Service**: assessments, assessment_results
3. **Roadmap Service**: roadmaps, roadmap_phases, roadmap_milestones, roadmap_courses, roadmap_templates
4. **Course Service**: courses, course_platforms, course_skills
5. **Job Service**: jobs, job_skills, job_platforms, market_insights, skill_demand
6. **Progress Service**: user_progress, course_completions, milestone_achievements, time_logs
7. **Career Tools Service**: resumes, portfolios
8. **Community Service**: posts, comments, votes (future)
9. **Notification Service**: notifications, notification_preferences

---

## Common Conventions

### Standard Fields (All Tables)
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
is_deleted BOOLEAN DEFAULT FALSE,
deleted_at TIMESTAMP WITH TIME ZONE
```

### Naming Conventions
- Tables: Plural, snake_case (e.g., `user_skills`, `roadmap_phases`)
- Columns: snake_case (e.g., `user_id`, `skill_name`)
- Indexes: `idx_{table}_{column(s)}` (e.g., `idx_users_email`)
- Foreign Keys: `fk_{table}_{referenced_table}` (e.g., `fk_user_skills_users`)

### Indexing Strategy
- Primary keys (UUID) automatically indexed
- Foreign keys indexed
- Frequently queried fields indexed
- Composite indexes for common query patterns
- Unique constraints where applicable

---

## 1. User Service Schema

### Table: `users`
**Purpose:** Core user account information

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Authentication
    auth0_id VARCHAR(255) UNIQUE NOT NULL, -- Auth0 user identifier
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    username VARCHAR(100) UNIQUE NOT NULL,
    
    -- Profile Information
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_number VARCHAR(20),
    
    -- Account Status
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,
    account_status VARCHAR(50) DEFAULT 'active', -- active, suspended, deleted
    
    -- Onboarding
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_step INTEGER DEFAULT 0,
    
    -- Preferences
    preferred_language VARCHAR(10) DEFAULT 'en', -- en, ar
    timezone VARCHAR(50) DEFAULT 'Africa/Cairo',
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_age CHECK (date_of_birth <= CURRENT_DATE - INTERVAL '13 years') -- Minimum age 13
);

-- Indexes
CREATE INDEX idx_users_email ON users(email) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_auth0_id ON users(auth0_id);
CREATE INDEX idx_users_username ON users(username) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_login ON users(last_login_at);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Table: `skills`
**Purpose:** Master list of all skills (predefined skill taxonomy)

```sql
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Skill Information
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL, -- URL-friendly version
    description TEXT,
    category VARCHAR(100) NOT NULL, -- technical, soft, business, design, etc.
    
    -- Taxonomy
    parent_skill_id UUID REFERENCES skills(id) ON DELETE SET NULL,
    skill_level VARCHAR(50), -- beginner, intermediate, advanced, expert
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    popularity_score INTEGER DEFAULT 0, -- For ranking/sorting
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_skills_name ON skills(name) WHERE is_deleted = FALSE;
CREATE INDEX idx_skills_slug ON skills(slug);
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_parent ON skills(parent_skill_id);
CREATE INDEX idx_skills_popularity ON skills(popularity_score DESC);

-- Sample Skills Data (Examples)
-- INSERT INTO skills (name, slug, category) VALUES
-- ('Python', 'python', 'technical'),
-- ('JavaScript', 'javascript', 'technical'),
-- ('Communication', 'communication', 'soft'),
-- ('Project Management', 'project-management', 'business');
```

### Table: `user_skills`
**Purpose:** Junction table linking users to their skills with proficiency levels

```sql
CREATE TABLE user_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    
    -- Skill Details
    skill_type VARCHAR(50) NOT NULL, -- hard, soft
    proficiency_level VARCHAR(50), -- beginner, intermediate, advanced, expert
    years_of_experience DECIMAL(4, 2), -- 0.5, 1.0, 2.5, etc.
    
    -- Source
    source VARCHAR(50) DEFAULT 'user_input', -- user_input, assessment, verified
    
    -- Verification (Future)
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(user_id, skill_id, is_deleted)
);

-- Indexes
CREATE INDEX idx_user_skills_user ON user_skills(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_user_skills_skill ON user_skills(skill_id);
CREATE INDEX idx_user_skills_type ON user_skills(skill_type);
CREATE INDEX idx_user_skills_proficiency ON user_skills(proficiency_level);
```

### Table: `user_preferences`
**Purpose:** User preferences and settings

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationship
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification Preferences
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    weekly_digest BOOLEAN DEFAULT TRUE,
    
    -- Privacy Settings
    profile_visibility VARCHAR(50) DEFAULT 'public', -- public, private, connections
    show_progress BOOLEAN DEFAULT TRUE,
    
    -- Learning Preferences
    preferred_learning_style VARCHAR(50), -- visual, auditory, reading, kinesthetic
    daily_learning_goal_minutes INTEGER DEFAULT 30,
    reminder_time TIME, -- Preferred time for learning reminders
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);
```

---

## 2. Assessment Service Schema

### Table: `assessments`
**Purpose:** Store completed assessments (entire assessment saved as user attribute)

```sql
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationship
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Assessment Type
    assessment_type VARCHAR(50) NOT NULL, -- quick, detailed, custom
    target_career VARCHAR(255) NOT NULL, -- Target job title/career
    
    -- Assessment Data (Stored as JSONB)
    questions JSONB NOT NULL, -- All questions and answer options
    user_responses JSONB NOT NULL, -- User's answers
    
    -- AI Processing
    ai_model_used VARCHAR(100), -- Which LLM was used
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_duration_seconds INTEGER,
    
    -- Metadata
    total_questions INTEGER NOT NULL,
    questions_answered INTEGER DEFAULT 0,
    time_taken_minutes INTEGER,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_assessments_user ON assessments(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_assessments_type ON assessments(assessment_type);
CREATE INDEX idx_assessments_status ON assessments(processing_status);
CREATE INDEX idx_assessments_career ON assessments(target_career);
CREATE INDEX idx_assessments_created ON assessments(created_at DESC);

-- GIN index for JSONB queries
CREATE INDEX idx_assessments_questions_gin ON assessments USING GIN (questions);
CREATE INDEX idx_assessments_responses_gin ON assessments USING GIN (user_responses);
```

### Table: `assessment_results`
**Purpose:** AI-generated insights and skill evaluations from assessments

```sql
CREATE TABLE assessment_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationship
    assessment_id UUID UNIQUE NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Overall Results
    overall_score DECIMAL(5, 2), -- 0.00 to 100.00
    proficiency_level VARCHAR(50), -- beginner, intermediate, advanced
    
    -- Skill Analysis (Stored as JSONB)
    skill_scores JSONB NOT NULL, -- { "skill_id": { "score": 85, "level": "advanced" } }
    strengths JSONB, -- Array of strength areas
    weaknesses JSONB, -- Array of areas for improvement
    skill_gaps JSONB, -- Skills needed for target career
    
    -- AI Insights
    ai_summary TEXT, -- Natural language summary
    recommendations JSONB, -- Array of recommendation objects
    next_steps JSONB, -- Suggested next actions
    
    -- Confidence Metrics
    confidence_score DECIMAL(5, 2), -- AI confidence in assessment (0-100)
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_assessment_results_assessment ON assessment_results(assessment_id);
CREATE INDEX idx_assessment_results_user ON assessment_results(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_assessment_results_score ON assessment_results(overall_score);

-- GIN indexes for JSONB
CREATE INDEX idx_assessment_results_skills_gin ON assessment_results USING GIN (skill_scores);
CREATE INDEX idx_assessment_results_strengths_gin ON assessment_results USING GIN (strengths);
CREATE INDEX idx_assessment_results_weaknesses_gin ON assessment_results USING GIN (weaknesses);
```

---

## 3. Roadmap Service Schema

### Table: `roadmap_templates`
**Purpose:** Pre-built roadmap templates for common career paths

```sql
CREATE TABLE roadmap_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template Information
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    target_career VARCHAR(255) NOT NULL,
    
    -- Template Details
    difficulty_level VARCHAR(50), -- beginner, intermediate, advanced
    estimated_duration_weeks INTEGER, -- Total estimated time
    required_hours_per_week INTEGER, -- Suggested time commitment
    
    -- Prerequisites
    prerequisites JSONB, -- Array of prerequisite skill IDs
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0, -- Track popularity
    average_completion_time_weeks DECIMAL(6, 2),
    
    -- Creator
    created_by UUID REFERENCES users(id) ON DELETE SET NULL, -- Admin/creator
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_roadmap_templates_slug ON roadmap_templates(slug);
CREATE INDEX idx_roadmap_templates_career ON roadmap_templates(target_career);
CREATE INDEX idx_roadmap_templates_active ON roadmap_templates(is_active) WHERE is_deleted = FALSE;
CREATE INDEX idx_roadmap_templates_usage ON roadmap_templates(usage_count DESC);
```

### Table: `roadmaps`
**Purpose:** User-specific roadmaps (personalized or from template)

```sql
CREATE TABLE roadmaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES roadmap_templates(id) ON DELETE SET NULL,
    assessment_id UUID REFERENCES assessments(id) ON DELETE SET NULL,
    
    -- Roadmap Information
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_career VARCHAR(255) NOT NULL,
    
    -- Roadmap Type
    roadmap_type VARCHAR(50) NOT NULL, -- template, personalized, custom
    
    -- Timeline
    estimated_duration_weeks INTEGER,
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, paused, completed, abandoned
    completion_percentage DECIMAL(5, 2) DEFAULT 0.00,
    
    -- AI Generation Details (for personalized roadmaps)
    ai_model_used VARCHAR(100),
    generation_parameters JSONB, -- Parameters used for generation
    
    -- Personalization
    user_modifications JSONB, -- Track user customizations
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_completion_percentage CHECK (completion_percentage BETWEEN 0 AND 100)
);

-- Indexes
CREATE INDEX idx_roadmaps_user ON roadmaps(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_roadmaps_template ON roadmaps(template_id);
CREATE INDEX idx_roadmaps_assessment ON roadmaps(assessment_id);
CREATE INDEX idx_roadmaps_status ON roadmaps(status);
CREATE INDEX idx_roadmaps_type ON roadmaps(roadmap_type);
CREATE INDEX idx_roadmaps_completion ON roadmaps(completion_percentage);
CREATE INDEX idx_roadmaps_created ON roadmaps(created_at DESC);
```

### Table: `roadmap_phases`
**Purpose:** High-level phases within a roadmap

```sql
CREATE TABLE roadmap_phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    
    -- Phase Information
    title VARCHAR(255) NOT NULL,
    description TEXT,
    phase_order INTEGER NOT NULL, -- Sequence within roadmap
    
    -- Timeline
    estimated_duration_weeks INTEGER,
    start_date DATE,
    end_date DATE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'not_started', -- not_started, in_progress, completed
    completion_percentage DECIMAL(5, 2) DEFAULT 0.00,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(roadmap_id, phase_order, is_deleted),
    CONSTRAINT chk_phase_completion CHECK (completion_percentage BETWEEN 0 AND 100)
);

-- Indexes
CREATE INDEX idx_roadmap_phases_roadmap ON roadmap_phases(roadmap_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_roadmap_phases_order ON roadmap_phases(roadmap_id, phase_order);
CREATE INDEX idx_roadmap_phases_status ON roadmap_phases(status);
```

### Table: `roadmap_milestones`
**Purpose:** Specific milestones within phases

```sql
CREATE TABLE roadmap_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    phase_id UUID NOT NULL REFERENCES roadmap_phases(id) ON DELETE CASCADE,
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE, -- Denormalized for queries
    
    -- Milestone Information
    title VARCHAR(255) NOT NULL,
    description TEXT,
    milestone_order INTEGER NOT NULL, -- Sequence within phase
    
    -- Skills Covered
    skills JSONB, -- Array of skill IDs covered in this milestone
    
    -- Timeline
    estimated_duration_days INTEGER,
    
    -- Status
    status VARCHAR(50) DEFAULT 'locked', -- locked, available, in_progress, completed
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(phase_id, milestone_order, is_deleted)
);

-- Indexes
CREATE INDEX idx_roadmap_milestones_phase ON roadmap_milestones(phase_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_roadmap_milestones_roadmap ON roadmap_milestones(roadmap_id);
CREATE INDEX idx_roadmap_milestones_order ON roadmap_milestones(phase_id, milestone_order);
CREATE INDEX idx_roadmap_milestones_status ON roadmap_milestones(status);
CREATE INDEX idx_roadmap_milestones_completed ON roadmap_milestones(is_completed);
```

### Table: `roadmap_courses`
**Purpose:** Courses assigned to milestones

```sql
CREATE TABLE roadmap_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    milestone_id UUID NOT NULL REFERENCES roadmap_milestones(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    
    -- Course Metadata
    course_order INTEGER NOT NULL, -- Sequence within milestone
    is_required BOOLEAN DEFAULT TRUE, -- Required or optional
    
    -- Status
    status VARCHAR(50) DEFAULT 'not_started', -- not_started, in_progress, completed, skipped
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(milestone_id, course_id, is_deleted)
);

-- Indexes
CREATE INDEX idx_roadmap_courses_milestone ON roadmap_courses(milestone_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_roadmap_courses_course ON roadmap_courses(course_id);
CREATE INDEX idx_roadmap_courses_order ON roadmap_courses(milestone_id, course_order);
CREATE INDEX idx_roadmap_courses_status ON roadmap_courses(status);
```

---

## 4. Course Service Schema

### Table: `course_platforms`
**Purpose:** External platforms hosting courses

```sql
CREATE TABLE course_platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Platform Information
    name VARCHAR(100) UNIQUE NOT NULL, -- Udemy, Coursera, YouTube, etc.
    slug VARCHAR(100) UNIQUE NOT NULL,
    website_url VARCHAR(500) NOT NULL,
    logo_url VARCHAR(500),
    
    -- API Configuration
    has_api BOOLEAN DEFAULT FALSE,
    api_endpoint VARCHAR(500),
    api_key_required BOOLEAN DEFAULT FALSE,
    
    -- Scraping Configuration
    requires_scraping BOOLEAN DEFAULT FALSE,
    scraping_enabled BOOLEAN DEFAULT FALSE,
    
    -- Platform Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_course_platforms_name ON course_platforms(name);
CREATE INDEX idx_course_platforms_slug ON course_platforms(slug);
CREATE INDEX idx_course_platforms_active ON course_platforms(is_active);
```

### Table: `courses`
**Purpose:** Course catalog (metadata from external platforms)

```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    platform_id UUID NOT NULL REFERENCES course_platforms(id) ON DELETE CASCADE,
    
    -- Course Identification
    external_id VARCHAR(255) NOT NULL, -- Platform's course ID
    external_url VARCHAR(1000) NOT NULL, -- Direct link to course
    
    -- Course Information
    title VARCHAR(500) NOT NULL,
    description TEXT,
    instructor_name VARCHAR(255),
    
    -- Course Details
    language VARCHAR(50) DEFAULT 'en',
    level VARCHAR(50), -- beginner, intermediate, advanced, all_levels
    duration_hours DECIMAL(6, 2),
    
    -- Pricing (Real-time data, minimal caching)
    price_usd DECIMAL(10, 2),
    currency_code VARCHAR(10),
    is_free BOOLEAN DEFAULT FALSE,
    
    -- Ratings (Cached from platform)
    average_rating DECIMAL(3, 2), -- 0.00 to 5.00
    total_ratings INTEGER DEFAULT 0,
    total_enrollments INTEGER DEFAULT 0,
    
    -- Content Details
    has_certificate BOOLEAN DEFAULT FALSE,
    has_subtitles BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    thumbnail_url VARCHAR(1000),
    last_updated_on_platform TIMESTAMP WITH TIME ZONE,
    
    -- Platform-Specific Data
    platform_metadata JSONB, -- Store additional platform-specific fields
    
    -- Caching
    last_fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE, -- Course still available on platform
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(platform_id, external_id, is_deleted)
);

-- Indexes
CREATE INDEX idx_courses_platform ON courses(platform_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_courses_external_id ON courses(platform_id, external_id);
CREATE INDEX idx_courses_title ON courses USING GIN (to_tsvector('english', title));
CREATE INDEX idx_courses_instructor ON courses(instructor_name);
CREATE INDEX idx_courses_level ON courses(level);
CREATE INDEX idx_courses_language ON courses(language);
CREATE INDEX idx_courses_rating ON courses(average_rating DESC);
CREATE INDEX idx_courses_enrollments ON courses(total_enrollments DESC);
CREATE INDEX idx_courses_free ON courses(is_free) WHERE is_free = TRUE;
CREATE INDEX idx_courses_active ON courses(is_active) WHERE is_deleted = FALSE;
CREATE INDEX idx_courses_last_fetched ON courses(last_fetched_at);
```

### Table: `course_skills`
**Purpose:** Skills taught in each course

```sql
CREATE TABLE course_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    
    -- Skill Coverage
    is_primary_skill BOOLEAN DEFAULT FALSE, -- Main skill vs secondary
    coverage_level VARCHAR(50), -- basic, intermediate, advanced, comprehensive
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(course_id, skill_id, is_deleted)
);

-- Indexes
CREATE INDEX idx_course_skills_course ON course_skills(course_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_course_skills_skill ON course_skills(skill_id);
CREATE INDEX idx_course_skills_primary ON course_skills(is_primary_skill) WHERE is_primary_skill = TRUE;
```

---

## 5. Job Service Schema

### Table: `job_platforms`
**Purpose:** Job listing platforms

```sql
CREATE TABLE job_platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Platform Information
    name VARCHAR(100) UNIQUE NOT NULL, -- Wuzzuf, LinkedIn, Bayt, etc.
    slug VARCHAR(100) UNIQUE NOT NULL,
    website_url VARCHAR(500) NOT NULL,
    logo_url VARCHAR(500),
    
    -- API/Scraping Configuration
    has_api BOOLEAN DEFAULT FALSE,
    api_endpoint VARCHAR(500),
    requires_scraping BOOLEAN DEFAULT TRUE,
    scraping_enabled BOOLEAN DEFAULT TRUE,
    
    -- Geographic Focus
    target_countries JSONB, -- ['Egypt', 'Saudi Arabia', etc.]
    
    -- Platform Status
    is_active BOOLEAN DEFAULT TRUE,
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_job_platforms_name ON job_platforms(name);
CREATE INDEX idx_job_platforms_slug ON job_platforms(slug);
CREATE INDEX idx_job_platforms_active ON job_platforms(is_active);
```

### Table: `jobs`
**Purpose:** Job listings scraped/fetched from platforms

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    platform_id UUID NOT NULL REFERENCES job_platforms(id) ON DELETE CASCADE,
    
    -- Job Identification
    external_id VARCHAR(255) NOT NULL, -- Platform's job ID
    external_url VARCHAR(1000) NOT NULL, -- Direct link to job posting
    
    -- Job Information
    title VARCHAR(500) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    company_logo_url VARCHAR(1000),
    
    -- Job Description
    description TEXT,
    requirements TEXT,
    responsibilities TEXT,
    
    -- Location
    location_city VARCHAR(100),
    location_country VARCHAR(100) DEFAULT 'Egypt',
    is_remote BOOLEAN DEFAULT FALSE,
    remote_type VARCHAR(50), -- fully_remote, hybrid, on_site
    
    -- Employment Details
    job_type VARCHAR(50), -- full_time, part_time, contract, internship, freelance
    experience_level VARCHAR(50), -- entry, mid, senior, lead, executive
    experience_years_min INTEGER,
    experience_years_max INTEGER,
    
    -- Salary
    salary_min DECIMAL(12, 2),
    salary_max DECIMAL(12, 2),
    salary_currency VARCHAR(10) DEFAULT 'EGP',
    salary_period VARCHAR(50), -- yearly, monthly, hourly
    salary_disclosed BOOLEAN DEFAULT FALSE,
    
    -- Application Details
    application_deadline DATE,
    posted_date DATE,
    
    -- Platform-Specific Data
    platform_metadata JSONB, -- Additional platform-specific fields
    
    -- Caching
    last_fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cache_expires_at TIMESTAMP WITH TIME ZONE, -- For 24-hour cache
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE, -- Job still available
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(platform_id, external_id, is_deleted)
);

-- Indexes
CREATE INDEX idx_jobs_platform ON jobs(platform_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_jobs_external_id ON jobs(platform_id, external_id);
CREATE INDEX idx_jobs_title ON jobs USING GIN (to_tsvector('english', title));
CREATE INDEX idx_jobs_company ON jobs(company_name);
CREATE INDEX idx_jobs_location_city ON jobs(location_city);
CREATE INDEX idx_jobs_location_country ON jobs(location_country);
CREATE INDEX idx_jobs_remote ON jobs(is_remote) WHERE is_remote = TRUE;
CREATE INDEX idx_jobs_type ON jobs(job_type);
CREATE INDEX idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_active ON jobs(is_active) WHERE is_deleted = FALSE;
CREATE INDEX idx_jobs_cache_expires ON jobs(cache_expires_at);
CREATE INDEX idx_jobs_description_fts ON jobs USING GIN (to_tsvector('english', description));
```

### Table: `job_skills`
**Purpose:** Skills required for jobs (extracted via NLP/LLM)

```sql
CREATE TABLE job_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    
    -- Skill Requirements
    is_required BOOLEAN DEFAULT TRUE, -- Required vs preferred
    proficiency_level VARCHAR(50), -- beginner, intermediate, advanced, expert
    years_of_experience INTEGER,
    
    -- Extraction Metadata
    extraction_confidence DECIMAL(5, 2), -- AI confidence (0-100)
    extracted_by VARCHAR(100), -- nlp_model, llm, manual
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(job_id, skill_id, is_deleted)
);

-- Indexes
CREATE INDEX idx_job_skills_job ON job_skills(job_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_job_skills_skill ON job_skills(skill_id);
CREATE INDEX idx_job_skills_required ON job_skills(is_required) WHERE is_required = TRUE;
CREATE INDEX idx_job_skills_proficiency ON job_skills(proficiency_level);
```

### Table: `market_insights`
**Purpose:** Aggregated market analysis and trends

```sql
CREATE TABLE market_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Time Period
    date DATE NOT NULL,
    period_type VARCHAR(50) NOT NULL, -- daily, weekly, monthly
    
    -- Geographic Scope
    country VARCHAR(100) DEFAULT 'Egypt',
    city VARCHAR(100),
    
    -- Market Metrics
    total_active_jobs INTEGER DEFAULT 0,
    new_jobs_posted INTEGER DEFAULT 0,
    jobs_expired INTEGER DEFAULT 0,
    
    -- Top Categories (JSONB)
    top_job_titles JSONB, -- [{ "title": "Software Engineer", "count": 150 }]
    top_companies JSONB, -- [{ "company": "Company A", "job_count": 50 }]
    top_skills_demanded JSONB, -- [{ "skill": "Python", "demand_count": 200 }]
    
    -- Salary Insights
    average_salary_disclosed DECIMAL(12, 2),
    salary_range_min DECIMAL(12, 2),
    salary_range_max DECIMAL(12, 2),
    
    -- Remote Work Trends
    remote_jobs_percentage DECIMAL(5, 2),
    
    -- Cache TTL
    cache_expires_at TIMESTAMP WITH TIME ZONE, -- 7 days
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(date, period_type, country, city, is_deleted)
);

-- Indexes
CREATE INDEX idx_market_insights_date ON market_insights(date DESC);
CREATE INDEX idx_market_insights_period ON market_insights(period_type);
CREATE INDEX idx_market_insights_country ON market_insights(country);
CREATE INDEX idx_market_insights_cache ON market_insights(cache_expires_at);
```

### Table: `skill_demand`
**Purpose:** Track demand for specific skills over time

```sql
CREATE TABLE skill_demand (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    
    -- Time Period
    date DATE NOT NULL,
    period_type VARCHAR(50) NOT NULL, -- daily, weekly, monthly
    
    -- Geographic Scope
    country VARCHAR(100) DEFAULT 'Egypt',
    
    -- Demand Metrics
    job_postings_count INTEGER DEFAULT 0, -- Number of jobs requiring this skill
    demand_trend VARCHAR(50), -- rising, falling, stable
    demand_change_percentage DECIMAL(6, 2), -- Compared to previous period
    
    -- Skill Context
    most_common_job_titles JSONB, -- Jobs that commonly require this skill
    average_experience_required DECIMAL(4, 2),
    
    -- Salary Correlation
    average_salary_with_skill DECIMAL(12, 2),
    
    -- Cache TTL
    cache_expires_at TIMESTAMP WITH TIME ZONE, -- 7 days
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(skill_id, date, period_type, country, is_deleted)
);

-- Indexes
CREATE INDEX idx_skill_demand_skill ON skill_demand(skill_id);
CREATE INDEX idx_skill_demand_date ON skill_demand(date DESC);
CREATE INDEX idx_skill_demand_period ON skill_demand(period_type);
CREATE INDEX idx_skill_demand_country ON skill_demand(country);
CREATE INDEX idx_skill_demand_count ON skill_demand(job_postings_count DESC);
CREATE INDEX idx_skill_demand_trend ON skill_demand(demand_trend);
```

---

## 6. Progress Service Schema

### Table: `user_progress`
**Purpose:** Overall user progress on their roadmap

```sql
CREATE TABLE user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    
    -- Progress Metrics
    overall_completion_percentage DECIMAL(5, 2) DEFAULT 0.00,
    phases_completed INTEGER DEFAULT 0,
    milestones_completed INTEGER DEFAULT 0,
    courses_completed INTEGER DEFAULT 0,
    
    -- Time Tracking
    total_learning_hours DECIMAL(10, 2) DEFAULT 0.00,
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_activity_date DATE,
    
    -- Current Status
    current_phase_id UUID REFERENCES roadmap_phases(id) ON DELETE SET NULL,
    current_milestone_id UUID REFERENCES roadmap_milestones(id) ON DELETE SET NULL,
    
    -- Pace Tracking
    average_hours_per_week DECIMAL(6, 2),
    on_track BOOLEAN DEFAULT TRUE, -- Meeting expected pace
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(user_id, roadmap_id, is_deleted),
    CONSTRAINT chk_user_progress_completion CHECK (overall_completion_percentage BETWEEN 0 AND 100)
);

-- Indexes
CREATE INDEX idx_user_progress_user ON user_progress(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_user_progress_roadmap ON user_progress(roadmap_id);
CREATE INDEX idx_user_progress_completion ON user_progress(overall_completion_percentage);
CREATE INDEX idx_user_progress_last_activity ON user_progress(last_activity_date DESC);
CREATE INDEX idx_user_progress_streak ON user_progress(current_streak_days DESC);
```

### Table: `course_completions`
**Purpose:** Track completed courses

```sql
CREATE TABLE course_completions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    roadmap_course_id UUID REFERENCES roadmap_courses(id) ON DELETE SET NULL, -- If part of roadmap
    
    -- Completion Details
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    time_spent_hours DECIMAL(8, 2),
    
    -- Progress
    completion_percentage DECIMAL(5, 2) DEFAULT 100.00, -- Usually 100 when completed
    
    -- User Feedback
    user_rating INTEGER, -- 1-5 stars
    user_review TEXT,
    would_recommend BOOLEAN,
    
    -- Certificate
    has_certificate BOOLEAN DEFAULT FALSE,
    certificate_url VARCHAR(1000),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(user_id, course_id, is_deleted),
    CONSTRAINT chk_course_completion_percentage CHECK (completion_percentage BETWEEN 0 AND 100),
    CONSTRAINT chk_course_completion_rating CHECK (user_rating BETWEEN 1 AND 5)
);

-- Indexes
CREATE INDEX idx_course_completions_user ON course_completions(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_course_completions_course ON course_completions(course_id);
CREATE INDEX idx_course_completions_roadmap_course ON course_completions(roadmap_course_id);
CREATE INDEX idx_course_completions_date ON course_completions(completed_at DESC);
CREATE INDEX idx_course_completions_rating ON course_completions(user_rating);
```

### Table: `milestone_achievements`
**Purpose:** Track completed milestones

```sql
CREATE TABLE milestone_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    milestone_id UUID NOT NULL REFERENCES roadmap_milestones(id) ON DELETE CASCADE,
    
    -- Achievement Details
    achieved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    time_to_complete_days INTEGER, -- Days taken from milestone unlock to completion
    
    -- Badge/Reward (Future)
    badge_awarded BOOLEAN DEFAULT FALSE,
    badge_type VARCHAR(100),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(user_id, milestone_id, is_deleted)
);

-- Indexes
CREATE INDEX idx_milestone_achievements_user ON milestone_achievements(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_milestone_achievements_milestone ON milestone_achievements(milestone_id);
CREATE INDEX idx_milestone_achievements_date ON milestone_achievements(achieved_at DESC);
```

### Table: `time_logs`
**Purpose:** Detailed time tracking for learning activities

```sql
CREATE TABLE time_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    roadmap_id UUID REFERENCES roadmaps(id) ON DELETE CASCADE,
    
    -- Time Details
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER NOT NULL,
    
    -- Activity Type
    activity_type VARCHAR(50) NOT NULL, -- course, practice, reading, project
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_time_log_duration CHECK (duration_minutes > 0 AND duration_minutes <= 1440), -- Max 24 hours
    CONSTRAINT chk_time_log_chronology CHECK (ended_at > started_at)
);

-- Indexes
CREATE INDEX idx_time_logs_user ON time_logs(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_time_logs_course ON time_logs(course_id);
CREATE INDEX idx_time_logs_roadmap ON time_logs(roadmap_id);
CREATE INDEX idx_time_logs_started ON time_logs(started_at DESC);
CREATE INDEX idx_time_logs_activity ON time_logs(activity_type);
CREATE INDEX idx_time_logs_user_date ON time_logs(user_id, started_at DESC);
```

---

## 7. Career Tools Service Schema

### Table: `resumes`
**Purpose:** User resumes (stored as database attributes)

```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Resume Information
    title VARCHAR(255) NOT NULL,
    template_name VARCHAR(100),
    
    -- Resume Data (Stored as JSONB)
    personal_info JSONB NOT NULL, -- Name, contact, summary, etc.
    work_experience JSONB, -- Array of job objects
    education JSONB, -- Array of education objects
    skills JSONB, -- Array of skills with proficiency
    certifications JSONB, -- Array of certifications
    projects JSONB, -- Array of projects
    languages JSONB, -- Array of languages with proficiency
    
    -- ATS Optimization
    is_ats_optimized BOOLEAN DEFAULT FALSE,
    ats_score DECIMAL(5, 2), -- 0-100 score
    ats_suggestions JSONB, -- AI-generated improvement suggestions
    
    -- File Storage (Stored in database initially)
    pdf_data BYTEA, -- Resume as PDF binary
    docx_data BYTEA, -- Resume as DOCX binary
    
    -- Metadata
    is_primary BOOLEAN DEFAULT FALSE, -- User's primary resume
    version INTEGER DEFAULT 1,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_resume_ats_score CHECK (ats_score BETWEEN 0 AND 100)
);

-- Indexes
CREATE INDEX idx_resumes_user ON resumes(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_resumes_primary ON resumes(user_id, is_primary) WHERE is_primary = TRUE;
CREATE INDEX idx_resumes_ats_score ON resumes(ats_score DESC);
CREATE INDEX idx_resumes_created ON resumes(created_at DESC);
```

### Table: `portfolios`
**Purpose:** User portfolios

```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Portfolio Information
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Portfolio Data (Stored as JSONB)
    projects JSONB, -- Array of project objects with details
    achievements JSONB, -- Array of achievements
    testimonials JSONB, -- Array of testimonials/recommendations
    
    -- Customization
    theme VARCHAR(100) DEFAULT 'default',
    custom_styles JSONB, -- Custom CSS/styling options
    
    -- Visibility
    is_public BOOLEAN DEFAULT TRUE,
    custom_url_slug VARCHAR(100) UNIQUE, -- For public portfolios
    
    -- Analytics (Future)
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_portfolios_user ON portfolios(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_portfolios_slug ON portfolios(custom_url_slug) WHERE is_public = TRUE;
CREATE INDEX idx_portfolios_public ON portfolios(is_public) WHERE is_public = TRUE;
```

---

## 8. Community Service Schema (Future - Nice to Have)

### Table: `posts`
**Purpose:** Community posts

```sql
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Post Content
    title VARCHAR(500),
    content TEXT NOT NULL,
    post_type VARCHAR(50) DEFAULT 'discussion', -- discussion, question, experience, tip
    
    -- Categorization
    tags JSONB, -- Array of tag strings
    related_skills JSONB, -- Array of skill IDs
    
    -- Engagement Metrics
    view_count INTEGER DEFAULT 0,
    upvote_count INTEGER DEFAULT 0,
    downvote_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- Status
    is_pinned BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    
    -- Moderation
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    moderation_status VARCHAR(50) DEFAULT 'approved', -- pending, approved, rejected
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_posts_user ON posts(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_posts_type ON posts(post_type);
CREATE INDEX idx_posts_created ON posts(created_at DESC);
CREATE INDEX idx_posts_upvotes ON posts(upvote_count DESC);
CREATE INDEX idx_posts_pinned ON posts(is_pinned) WHERE is_pinned = TRUE;
CREATE INDEX idx_posts_featured ON posts(is_featured) WHERE is_featured = TRUE;
CREATE INDEX idx_posts_content_fts ON posts USING GIN (to_tsvector('english', title || ' ' || content));
```

### Table: `comments`
**Purpose:** Comments on posts

```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE, -- For threaded comments
    
    -- Comment Content
    content TEXT NOT NULL,
    
    -- Engagement
    upvote_count INTEGER DEFAULT 0,
    downvote_count INTEGER DEFAULT 0,
    
    -- Moderation
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_comments_post ON comments(post_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_comments_parent ON comments(parent_comment_id);
CREATE INDEX idx_comments_created ON comments(created_at DESC);
```

### Table: `votes`
**Purpose:** User votes on posts and comments

```sql
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    
    -- Vote Type
    vote_type VARCHAR(20) NOT NULL, -- upvote, downvote
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_vote_target CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL) OR
        (post_id IS NULL AND comment_id IS NOT NULL)
    ),
    CONSTRAINT chk_vote_type CHECK (vote_type IN ('upvote', 'downvote')),
    UNIQUE(user_id, post_id, is_deleted),
    UNIQUE(user_id, comment_id, is_deleted)
);

-- Indexes
CREATE INDEX idx_votes_user ON votes(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_votes_post ON votes(post_id);
CREATE INDEX idx_votes_comment ON votes(comment_id);
CREATE INDEX idx_votes_type ON votes(vote_type);
```

---

## 9. Notification Service Schema

### Table: `notifications`
**Purpose:** Store all user notifications

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification Details
    notification_type VARCHAR(100) NOT NULL, -- milestone_achieved, course_completed, job_match, etc.
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Related Entities (Polymorphic)
    related_entity_type VARCHAR(100), -- roadmap, course, job, post, etc.
    related_entity_id UUID,
    
    -- Action/Link
    action_url VARCHAR(1000), -- Where to redirect user on click
    action_text VARCHAR(100), -- Button/link text
    
    -- Notification Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Delivery
    delivery_status VARCHAR(50) DEFAULT 'sent', -- sent, failed, pending
    
    -- Priority
    priority VARCHAR(50) DEFAULT 'normal', -- low, normal, high, urgent
    
    -- Metadata
    metadata JSONB, -- Additional context data
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_notifications_user ON notifications(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
CREATE INDEX idx_notifications_priority ON notifications(priority);
CREATE INDEX idx_notifications_entity ON notifications(related_entity_type, related_entity_id);
```

### Table: `notification_preferences`
**Purpose:** User notification preferences

```sql
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Channel Preferences
    in_app_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT FALSE, -- Future
    
    -- Notification Type Preferences (JSONB for flexibility)
    preferences JSONB DEFAULT '{}', -- { "milestone_achieved": true, "job_match": false, etc. }
    
    -- Frequency Settings
    digest_frequency VARCHAR(50) DEFAULT 'weekly', -- daily, weekly, monthly, never
    quiet_hours_start TIME, -- Don't send during these hours
    quiet_hours_end TIME,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_notification_preferences_user ON notification_preferences(user_id);
```

---

## Database Relationships Diagram (Entity Relationship Overview)

```
users (1) ─────< (N) user_skills ───> (1) skills
  │
  ├─────< (N) assessments
  │            │
  │            └────< (1) assessment_results
  │
  ├─────< (N) roadmaps ───> (1) roadmap_templates
  │            │
  │            ├─────< (N) roadmap_phases
  │            │               │
  │            │               └─────< (N) roadmap_milestones
  │            │                               │
  │            │                               └─────< (N) roadmap_courses ───> (1) courses
  │            │
  │            └─────< (1) user_progress
  │                           │
  │                           ├─────< (N) course_completions ───> (1) courses
  │                           ├─────< (N) milestone_achievements ───> (1) roadmap_milestones
  │                           └─────< (N) time_logs
  │
  ├─────< (N) resumes
  ├─────< (N) portfolios
  ├─────< (N) posts
  ├─────< (N) comments
  ├─────< (N) votes
  └─────< (N) notifications

courses (N) ────> (1) course_platforms
courses (N) ────< (N) course_skills ───> (1) skills

jobs (N) ────> (1) job_platforms
jobs (N) ────< (N) job_skills ───> (1) skills

skill_demand (N) ────> (1) skills
```

---

## Data Migration & Seeding Strategy

### Initial Data Setup

**1. Skills Master Data**
```sql
-- Populate skills table with comprehensive skill taxonomy
-- Categories: technical, soft, business, design, data, marketing, etc.
-- Source: O*NET, LinkedIn Skills, industry standards
```

**2. Course Platforms**
```sql
INSERT INTO course_platforms (name, slug, website_url, has_api, requires_scraping)
VALUES
    ('Udemy', 'udemy', 'https://www.udemy.com', TRUE, FALSE),
    ('Coursera', 'coursera', 'https://www.coursera.org', TRUE, FALSE),
    ('YouTube', 'youtube', 'https://www.youtube.com', TRUE, FALSE),
    ('edX', 'edx', 'https://www.edx.org', TRUE, FALSE);
```

**3. Job Platforms**
```sql
INSERT INTO job_platforms (name, slug, website_url, has_api, requires_scraping)
VALUES
    ('Wuzzuf', 'wuzzuf', 'https://wuzzuf.net', FALSE, TRUE),
    ('Bayt', 'bayt', 'https://www.bayt.com', FALSE, TRUE),
    ('LinkedIn', 'linkedin', 'https://www.linkedin.com/jobs', FALSE, TRUE);
```

**4. Roadmap Templates**
```sql
-- Create pre-built roadmaps for popular careers
-- Examples: Full-Stack Developer, Data Scientist, Product Manager, UI/UX Designer
```

---

## Performance Optimization Guidelines

### Indexing Strategy
- **Primary keys**: Automatically indexed (UUID)
- **Foreign keys**: Always indexed for join performance
- **Frequently filtered columns**: Add indexes (e.g., `is_deleted`, `is_active`)
- **Search fields**: Full-text search indexes (GIN) on text columns
- **JSONB columns**: GIN indexes for querying nested data
- **Composite indexes**: For common multi-column queries

### Query Optimization
- Use `EXPLAIN ANALYZE` to identify slow queries
- Avoid `SELECT *`, fetch only needed columns
- Use pagination for large result sets
- Leverage database views for complex queries
- Use materialized views for expensive aggregations

### Connection Pooling
- Use PgBouncer for connection pooling
- Limit max connections per service
- Monitor connection usage

### Partitioning (Future)
- Partition large tables by date (e.g., `time_logs`, `notifications`)
- Archive old data to separate tables

---

## Backup & Recovery Strategy

### Backup Schedule
- **Daily**: Full database backup (retain 7 days)
- **Hourly**: Incremental backup (retain 24 hours)
- **Weekly**: Archive backup (retain 4 weeks)
- **Monthly**: Long-term archive (retain 12 months)

### Point-in-Time Recovery
- Enable WAL (Write-Ahead Logging)
- Configure continuous archiving
- Test recovery procedures quarterly

### Backup Storage
- Store backups in separate location from primary database
- Encrypt backups at rest
- Test restore regularly

---

## Data Retention & Privacy

### GDPR Compliance
- Implement soft deletes (`is_deleted` flag)
- Provide user data export (JSON format)
- Support complete data deletion on request
- Anonymize data for analytics (remove PII)

### Data Retention Policies
- **Active users**: No deletion
- **Inactive users (2+ years)**: Notify before archiving
- **Deleted accounts**: Hard delete after 90 days
- **Logs**: Retain 12 months, then archive or delete
- **Notifications**: Delete read notifications after 6 months

---

## Schema Version Control

### Migration Management
- Use Django migrations for schema changes
- Version control all migrations
- Test migrations on staging before production
- Create rollback scripts for critical changes

### Migration Best Practices
- Make migrations backward compatible when possible
- Split large migrations into smaller chunks
- Add indexes in separate migrations (avoid locking)
- Use `CONCURRENTLY` for index creation in production

---

*Last Updated: November 2025*  
*Status: Database Design Phase - Schema subject to refinement during development*
