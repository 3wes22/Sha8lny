# Sha8alny - Coding Standards & Best Practices

## Overview
This document establishes coding conventions, best practices, and quality standards for the Sha8alny development team. Consistent code style improves readability, maintainability, and collaboration.

---

## General Principles

### Code Philosophy
1. **Readability First**: Code is read more often than written
2. **Keep It Simple**: Favor simplicity over cleverness
3. **DRY (Don't Repeat Yourself)**: Extract common functionality
4. **YAGNI (You Aren't Gonna Need It)**: Don't build features until needed
5. **Separation of Concerns**: Each component should have a single responsibility
6. **Test-Driven Development**: Write tests for critical business logic

### Code Review Culture
- All code must be reviewed before merging
- Be constructive and respectful in reviews
- Review for logic, not just syntax
- Ask questions, don't just criticize
- Learn from each other

---

## Python / Django Standards

### Style Guide
**Primary Reference**: [PEP 8 – Style Guide for Python Code](https://pep8.org/)

### Key Conventions

**1. Naming Conventions**
```python
# Classes: PascalCase
class UserService:
    pass

class AssessmentResult:
    pass

# Functions and methods: snake_case
def generate_roadmap(user_id, assessment_id):
    pass

def calculate_skill_score():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_CACHE_TTL = 3600

# Private methods: prefix with underscore
def _internal_helper_method():
    pass

# Variables: snake_case
user_progress = None
total_courses_completed = 0
```

**2. Imports**
```python
# Standard library imports first
import os
import sys
from datetime import datetime, timedelta

# Third-party imports second
import requests
from django.db import models
from rest_framework import serializers

# Local application imports last
from apps.users.models import User
from apps.assessments.services import AssessmentService
from utils.cache import cache_result

# Avoid wildcard imports
# ❌ from module import *
# ✅ from module import SpecificClass, specific_function
```

**3. Line Length**
- Maximum 100 characters per line (not the strict 79 from PEP 8)
- Break long lines logically

```python
# ❌ Bad - too long
user_roadmap = RoadmapService.generate_personalized_roadmap(user_id=user.id, assessment_results=assessment_results, target_career=user.target_career, preferences=user_preferences)

# ✅ Good - broken logically
user_roadmap = RoadmapService.generate_personalized_roadmap(
    user_id=user.id,
    assessment_results=assessment_results,
    target_career=user.target_career,
    preferences=user_preferences
)
```

**4. Docstrings**
Use Google-style docstrings for functions and classes

```python
def generate_assessment_questions(user_id: str, target_career: str, difficulty: str = "medium") -> dict:
    """
    Generate AI-powered assessment questions for a user.
    
    Args:
        user_id (str): UUID of the user taking the assessment
        target_career (str): Target career path for the assessment
        difficulty (str, optional): Difficulty level. Defaults to "medium".
    
    Returns:
        dict: Dictionary containing questions array and metadata
        
    Raises:
        ValidationError: If user_id or target_career is invalid
        AIServiceError: If AI model fails to generate questions
        
    Example:
        >>> questions = generate_assessment_questions(
        ...     user_id="123e4567-e89b-12d3-a456-426614174000",
        ...     target_career="Software Engineer"
        ... )
        >>> print(questions['total_questions'])
        20
    """
    pass
```

**5. Type Hints**
Use type hints for function parameters and return values

```python
from typing import List, Dict, Optional, Union
from uuid import UUID

def calculate_roadmap_duration(
    phases: List[Dict[str, any]],
    user_pace: str
) -> int:
    """Calculate total roadmap duration in weeks."""
    pass

def get_user_by_id(user_id: UUID) -> Optional[User]:
    """Retrieve user or return None if not found."""
    pass
```

### Django-Specific Conventions

**1. Model Structure**
```python
from django.db import models
from uuid import uuid4

class Assessment(models.Model):
    """
    Represents a user assessment.
    
    An assessment evaluates a user's skills for a specific career path.
    """
    
    # Primary Key (always use UUID)
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Foreign Keys
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    
    # Fields (grouped logically)
    assessment_type = models.CharField(max_length=50)
    target_career = models.CharField(max_length=255)
    questions = models.JSONField()
    
    # Status fields
    processing_status = models.CharField(
        max_length=50,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]
    )
    
    # Audit fields (always last)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'assessments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['processing_status']),
        ]
    
    def __str__(self):
        return f"Assessment {self.id} - {self.user.username}"
    
    def __repr__(self):
        return f"<Assessment id={self.id} user={self.user_id}>"
```

**2. Serializers**
```python
from rest_framework import serializers
from apps.assessments.models import Assessment

class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model."""
    
    # Custom fields
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id',
            'user',
            'user_name',
            'assessment_type',
            'target_career',
            'questions',
            'questions_count',
            'processing_status',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'user_name']
    
    def get_questions_count(self, obj):
        """Calculate number of questions in assessment."""
        return len(obj.questions.get('questions', []))
    
    def validate_target_career(self, value):
        """Validate target career is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Target career cannot be empty")
        return value.strip()
```

**3. Views**
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class AssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing assessments.
    
    Provides CRUD operations and custom actions for assessments.
    """
    
    queryset = Assessment.objects.filter(is_deleted=False)
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter assessments by current user."""
        return super().get_queryset().filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user from request when creating assessment."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit assessment responses.
        
        Triggers background processing of assessment results.
        """
        assessment = self.get_object()
        
        # Validation
        if assessment.processing_status == 'completed':
            return Response(
                {'error': 'Assessment already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update responses
        assessment.user_responses = request.data.get('responses', {})
        assessment.processing_status = 'processing'
        assessment.save()
        
        # Trigger background task
        from apps.assessments.tasks import process_assessment
        process_assessment.delay(str(assessment.id))
        
        return Response(
            {'message': 'Assessment submitted successfully'},
            status=status.HTTP_202_ACCEPTED
        )
```

**4. Services (Business Logic Layer)**
```python
from typing import Dict, List
from uuid import UUID
from apps.assessments.models import Assessment, AssessmentResult
from apps.ai.services import LLMService

class AssessmentService:
    """
    Service layer for assessment business logic.
    
    Encapsulates complex assessment-related operations.
    """
    
    @staticmethod
    def generate_questions(
        user_id: UUID,
        target_career: str,
        assessment_type: str = "detailed"
    ) -> Dict:
        """
        Generate assessment questions using AI.
        
        Args:
            user_id: UUID of the user
            target_career: Target career path
            assessment_type: Type of assessment (quick/detailed)
            
        Returns:
            Dictionary with generated questions
        """
        # Fetch user data
        user = User.objects.get(id=user_id)
        user_skills = user.user_skills.all()
        
        # Build AI prompt
        prompt = AssessmentService._build_assessment_prompt(
            target_career=target_career,
            user_skills=user_skills,
            assessment_type=assessment_type
        )
        
        # Call AI service
        llm_service = LLMService()
        questions = llm_service.generate_questions(prompt)
        
        return questions
    
    @staticmethod
    def _build_assessment_prompt(
        target_career: str,
        user_skills: List,
        assessment_type: str
    ) -> str:
        """Build prompt for AI question generation."""
        # Private helper method
        skills_text = ", ".join([skill.skill.name for skill in user_skills])
        return f"Generate {assessment_type} assessment for {target_career}..."
```

**5. Celery Tasks**
```python
from celery import shared_task
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_assessment(self, assessment_id: str) -> dict:
    """
    Process assessment and generate results.
    
    Args:
        assessment_id: UUID string of the assessment
        
    Returns:
        dict: Processing results
    """
    try:
        assessment = Assessment.objects.get(id=UUID(assessment_id))
        
        # Process assessment
        from apps.assessments.services import AssessmentService
        results = AssessmentService.process_assessment_responses(assessment)
        
        # Update status
        assessment.processing_status = 'completed'
        assessment.save()
        
        logger.info(f"Successfully processed assessment {assessment_id}")
        return {'status': 'success', 'assessment_id': assessment_id}
        
    except Exception as exc:
        logger.error(f"Error processing assessment {assessment_id}: {exc}")
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Error Handling

**1. Custom Exceptions**
```python
# apps/core/exceptions.py

class Sha8alnyException(Exception):
    """Base exception for Sha8alny platform."""
    pass

class AIServiceError(Sha8alnyException):
    """Raised when AI service fails."""
    pass

class InsufficientDataError(Sha8alnyException):
    """Raised when insufficient data for operation."""
    pass

# Usage
from apps.core.exceptions import AIServiceError

def call_ai_model():
    try:
        response = llm_api.generate()
    except Exception as e:
        raise AIServiceError(f"AI model failed: {str(e)}")
```

**2. Exception Handling in Views**
```python
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize error response format
        response.data = {
            'error': True,
            'message': str(exc),
            'details': response.data
        }
    
    return response

# In settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler'
}
```

### Testing Standards

**1. Test Structure**
```python
from django.test import TestCase
from apps.users.models import User
from apps.assessments.services import AssessmentService

class AssessmentServiceTestCase(TestCase):
    """Test cases for AssessmentService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com',
            full_name='Test User'
        )
    
    def tearDown(self):
        """Clean up after tests."""
        User.objects.all().delete()
    
    def test_generate_questions_success(self):
        """Test successful question generation."""
        questions = AssessmentService.generate_questions(
            user_id=self.user.id,
            target_career='Software Engineer'
        )
        
        self.assertIsNotNone(questions)
        self.assertIn('questions', questions)
        self.assertGreater(len(questions['questions']), 0)
    
    def test_generate_questions_invalid_user(self):
        """Test question generation with invalid user."""
        from uuid import uuid4
        
        with self.assertRaises(User.DoesNotExist):
            AssessmentService.generate_questions(
                user_id=uuid4(),
                target_career='Software Engineer'
            )
```

**2. Test Coverage**
- Aim for 80%+ test coverage for business logic
- 100% coverage for critical paths (authentication, payments, data integrity)
- Use `pytest-cov` for coverage reports

```bash
pytest --cov=apps --cov-report=html
```

---

## TypeScript / React Standards

### Style Guide
**Primary Reference**: [Airbnb React/JSX Style Guide](https://github.com/airbnb/javascript/tree/master/react)

### Key Conventions

**1. File Naming**
```
components/          # React components
├── Button.tsx       # PascalCase for components
├── UserProfile.tsx
└── RoadmapCard.tsx

hooks/               # Custom hooks
├── useAuth.ts       # camelCase with 'use' prefix
└── useFetchData.ts

utils/               # Utility functions
├── formatDate.ts    # camelCase
└── validation.ts

types/               # TypeScript types/interfaces
├── user.types.ts    # lowercase with .types.ts suffix
└── api.types.ts
```

**2. Component Structure**
```typescript
// components/AssessmentCard.tsx

import React from 'react';
import { Assessment } from '@/types/assessment.types';
import { Button } from '@/components/Button';
import styles from './AssessmentCard.module.css';

// Props interface
interface AssessmentCardProps {
  assessment: Assessment;
  onStart: (assessmentId: string) => void;
  onView: (assessmentId: string) => void;
  className?: string;
}

/**
 * AssessmentCard component displays assessment information.
 * 
 * @param props - Component props
 * @returns Rendered assessment card
 */
export const AssessmentCard: React.FC<AssessmentCardProps> = ({
  assessment,
  onStart,
  onView,
  className = '',
}) => {
  // Event handlers
  const handleStartClick = () => {
    onStart(assessment.id);
  };

  const handleViewClick = () => {
    onView(assessment.id);
  };

  // Render
  return (
    <div className={`${styles.card} ${className}`}>
      <h3 className={styles.title}>{assessment.targetCareer}</h3>
      <p className={styles.description}>{assessment.assessmentType}</p>
      
      <div className={styles.actions}>
        {assessment.status === 'pending' && (
          <Button onClick={handleStartClick} variant="primary">
            Start Assessment
          </Button>
        )}
        {assessment.status === 'completed' && (
          <Button onClick={handleViewClick} variant="secondary">
            View Results
          </Button>
        )}
      </div>
    </div>
  );
};
```

**3. Custom Hooks**
```typescript
// hooks/useAssessment.ts

import { useState, useEffect } from 'react';
import { Assessment } from '@/types/assessment.types';
import { assessmentApi } from '@/api/assessments';

interface UseAssessmentReturn {
  assessment: Assessment | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Custom hook to fetch and manage assessment data.
 * 
 * @param assessmentId - UUID of the assessment
 * @returns Assessment data, loading state, and error
 */
export const useAssessment = (assessmentId: string): UseAssessmentReturn => {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchAssessment = async () => {
    try {
      setLoading(true);
      const data = await assessmentApi.getById(assessmentId);
      setAssessment(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
      setAssessment(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessment();
  }, [assessmentId]);

  return {
    assessment,
    loading,
    error,
    refetch: fetchAssessment,
  };
};
```

**4. Type Definitions**
```typescript
// types/assessment.types.ts

/**
 * Assessment status values
 */
export type AssessmentStatus = 
  | 'pending' 
  | 'processing' 
  | 'completed' 
  | 'failed';

/**
 * Assessment type
 */
export type AssessmentType = 'quick' | 'detailed' | 'custom';

/**
 * Assessment entity
 */
export interface Assessment {
  id: string;
  userId: string;
  assessmentType: AssessmentType;
  targetCareer: string;
  questions: Question[];
  userResponses?: Record<string, any>;
  processingStatus: AssessmentStatus;
  createdAt: string;
  updatedAt: string;
}

/**
 * Question entity
 */
export interface Question {
  id: string;
  text: string;
  type: 'multiple_choice' | 'text' | 'rating';
  options?: string[];
  required: boolean;
}

/**
 * API response for assessment list
 */
export interface AssessmentListResponse {
  data: Assessment[];
  total: number;
  page: number;
  pageSize: number;
}
```

**5. API Service Layer**
```typescript
// api/assessments.ts

import axios from 'axios';
import { Assessment, AssessmentListResponse } from '@/types/assessment.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Assessment API service
 */
export const assessmentApi = {
  /**
   * Get all assessments for current user
   */
  getAll: async (): Promise<AssessmentListResponse> => {
    const response = await axios.get<AssessmentListResponse>(
      `${API_BASE_URL}/assessments/`
    );
    return response.data;
  },

  /**
   * Get assessment by ID
   */
  getById: async (id: string): Promise<Assessment> => {
    const response = await axios.get<Assessment>(
      `${API_BASE_URL}/assessments/${id}/`
    );
    return response.data;
  },

  /**
   * Create new assessment
   */
  create: async (data: Partial<Assessment>): Promise<Assessment> => {
    const response = await axios.post<Assessment>(
      `${API_BASE_URL}/assessments/`,
      data
    );
    return response.data;
  },

  /**
   * Submit assessment responses
   */
  submit: async (id: string, responses: Record<string, any>): Promise<void> => {
    await axios.post(
      `${API_BASE_URL}/assessments/${id}/submit/`,
      { responses }
    );
  },
};
```

### React Best Practices

**1. Component Organization**
```typescript
// ❌ Bad - everything in one component
function Dashboard() {
  const [user, setUser] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [progress, setProgress] = useState(null);
  
  // 500 lines of code...
}

// ✅ Good - split into smaller components
function Dashboard() {
  return (
    <div>
      <DashboardHeader />
      <UserProfile />
      <RoadmapOverview />
      <ProgressTracker />
      <RecentActivity />
    </div>
  );
}
```

**2. Props Destructuring**
```typescript
// ❌ Bad
function UserCard(props) {
  return <div>{props.user.name}</div>;
}

// ✅ Good
function UserCard({ user, onEdit, className }: UserCardProps) {
  return <div className={className}>{user.name}</div>;
}
```

**3. Conditional Rendering**
```typescript
// ✅ Use logical AND for simple conditions
{isLoading && <Spinner />}

// ✅ Use ternary for if-else
{isLoading ? <Spinner /> : <Content />}

// ✅ Use early returns for complex conditions
if (isLoading) return <Spinner />;
if (error) return <Error message={error.message} />;
return <Content />;
```

---

## Git Workflow & Commit Standards

### Branch Naming
```
main              # Production-ready code
develop           # Integration branch
feature/{ticket-id}-{short-description}
bugfix/{ticket-id}-{short-description}
hotfix/{ticket-id}-{short-description}

# Examples
feature/SHA-123-user-authentication
feature/SHA-124-assessment-generation
bugfix/SHA-125-roadmap-calculation-error
hotfix/SHA-126-critical-login-issue
```

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/)

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(assessment): add AI-powered question generation

Implement LLM integration for generating personalized assessment questions
based on target career and user skill level.

Closes SHA-123

---

fix(roadmap): correct completion percentage calculation

Fixed bug where roadmap completion was showing >100% when user
completed optional courses.

Fixes SHA-125

---

docs(api): update authentication endpoint documentation

Added examples for JWT token refresh flow and error responses.
```

### Pull Request Guidelines

**PR Title Format:**
```
[SHA-123] Add user authentication service
[SHA-124] Fix roadmap generation for edge cases
```

**PR Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issue
Closes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## Code Quality Tools

### Python Tools

**1. Linting**
```bash
# flake8 configuration (.flake8)
[flake8]
max-line-length = 100
exclude = migrations,__pycache__,venv
ignore = E203,W503

# Run linting
flake8 apps/
```

**2. Formatting**
```bash
# black configuration (pyproject.toml)
[tool.black]
line-length = 100
target-version = ['py311']
exclude = '''
/(
    migrations
  | __pycache__
  | venv
)/
'''

# Format code
black apps/
```

**3. Import Sorting**
```bash
# isort configuration (pyproject.toml)
[tool.isort]
profile = "black"
line_length = 100

# Sort imports
isort apps/
```

**4. Type Checking**
```bash
# mypy configuration (mypy.ini)
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True

# Run type checking
mypy apps/
```

### TypeScript/React Tools

**1. ESLint Configuration**
```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "airbnb",
    "airbnb-typescript",
    "plugin:@typescript-eslint/recommended"
  ],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "@typescript-eslint/explicit-function-return-type": "off",
    "import/prefer-default-export": "off"
  }
}
```

**2. Prettier Configuration**
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

Install: `pre-commit install`

---

## Security Best Practices

### 1. Never Commit Secrets
```python
# ❌ Bad
API_KEY = "sk-1234567890abcdef"

# ✅ Good
API_KEY = os.getenv('API_KEY')
```

### 2. Input Validation
```python
# Always validate user input
from rest_framework import serializers

class UserInputSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    age = serializers.IntegerField(min_value=13, max_value=120)
    
    def validate_email(self, value):
        # Custom validation
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
```

### 3. SQL Injection Prevention
```python
# ❌ Bad - vulnerable to SQL injection
User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ Good - use ORM or parameterized queries
User.objects.filter(id=user_id)
```

### 4. XSS Prevention
```typescript
// React automatically escapes content
<div>{user.name}</div>  // Safe

// ❌ Dangerous - only use when necessary
<div dangerouslySetInnerHTML={{ __html: content }} />

// ✅ Sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }} />
```

---

## Performance Guidelines

### Django Performance

**1. Database Query Optimization**
```python
# ❌ Bad - N+1 query problem
users = User.objects.all()
for user in users:
    print(user.roadmap.title)  # Separate query for each user

# ✅ Good - use select_related
users = User.objects.select_related('roadmap').all()
for user in users:
    print(user.roadmap.title)  # Single query with JOIN

# ✅ Use prefetch_related for reverse FKs and M2M
roadmaps = Roadmap.objects.prefetch_related('phases__milestones').all()
```

**2. Caching**
```python
from django.core.cache import cache

def get_market_insights(country: str):
    cache_key = f"market_insights_{country}"
    
    # Try cache first
    insights = cache.get(cache_key)
    if insights is not None:
        return insights
    
    # Compute if not cached
    insights = compute_market_insights(country)
    
    # Cache for 7 days
    cache.set(cache_key, insights, 60 * 60 * 24 * 7)
    
    return insights
```

### React Performance

**1. Memoization**
```typescript
import { useMemo, useCallback } from 'react';

function ExpensiveComponent({ data, onUpdate }) {
  // Memoize expensive calculations
  const processedData = useMemo(() => {
    return expensiveOperation(data);
  }, [data]);

  // Memoize callbacks
  const handleClick = useCallback(() => {
    onUpdate(processedData);
  }, [processedData, onUpdate]);

  return <div onClick={handleClick}>{processedData}</div>;
}
```

**2. Code Splitting**
```typescript
import dynamic from 'next/dynamic';

// Lazy load heavy components
const RoadmapVisualization = dynamic(
  () => import('@/components/RoadmapVisualization'),
  { loading: () => <Spinner /> }
);
```

---

## Documentation Standards

### 1. README Files
Every major module should have a README explaining:
- Purpose of the module
- How to use it
- Examples
- Dependencies

### 2. API Documentation
Use Django REST Framework's built-in documentation or Swagger/OpenAPI

### 3. Inline Comments
```python
# ✅ Good comments explain WHY, not WHAT
# We use exponential backoff because the external API has rate limits
retry_delay = 2 ** attempt

# ❌ Bad comments explain the obvious
# Set retry delay to 2 to the power of attempt
retry_delay = 2 ** attempt
```

---

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run linting
        run: |
          flake8 apps/
          black --check apps/
      
      - name: Run tests
        run: |
          pytest --cov=apps --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

*Last Updated: November 2025*  
*These standards are living documents and should be updated as the team grows and learns.*
