# SkillPath AI - API Specification

> **Document Version:** 1.0
> **Last Updated:** November 4, 2025
> **API Style:** RESTful
> **Base URL:** `https://api.skillpath-ai.com/v1`

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Endpoint Categories](#endpoint-categories)
6. [Detailed Endpoints](#detailed-endpoints)

---

## API Overview

### REST Principles

- **Resource-based URLs:** `/api/v1/users`, `/api/v1/assessments`
- **HTTP Methods:** GET, POST, PUT, PATCH, DELETE
- **Status Codes:** Standard HTTP status codes
- **JSON:** All requests and responses use JSON

### Base URL

```
Development:  http://localhost:3000/api/v1
Production:   https://api.skillpath-ai.com/api/v1
```

### Common Headers

```http
Content-Type: application/json
Authorization: Bearer <access_token>
Accept: application/json
X-API-Version: v1
```

### Request Format

```json
{
  "data": {
    // Request payload
  }
}
```

### Response Format

**Success Response:**
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2025-11-04T10:30:00Z",
    "version": "1.0"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-11-04T10:30:00Z",
    "version": "1.0"
  }
}
```

---

## Authentication

### Authentication Flow

**JWT (JSON Web Token) based authentication**

1. User registers/logs in → Receives access token + refresh token
2. Client includes access token in `Authorization` header
3. Access token expires (15 min) → Use refresh token to get new access token
4. Refresh token expires (7 days) → User must log in again

### Token Types

**Access Token:**
- Short-lived (15 minutes)
- Include in Authorization header: `Bearer <token>`
- Contains: `userId`, `email`, `role`, `permissions`

**Refresh Token:**
- Long-lived (7 days)
- Stored in httpOnly cookie
- Used to obtain new access token

### Protected Routes

Add `Authorization: Bearer <access_token>` header to all protected endpoints.

**Public Endpoints (No auth required):**
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/forgot-password`
- `GET /assessments` (list public assessments)
- `GET /courses` (browse courses)
- `GET /jobs` (search jobs)

**Protected Endpoints:**
All other endpoints require authentication.

---

## Error Handling

### Standard HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| **200** | OK | Successful GET, PUT, PATCH |
| **201** | Created | Successful POST (resource created) |
| **204** | No Content | Successful DELETE |
| **400** | Bad Request | Invalid request format, validation error |
| **401** | Unauthorized | Missing or invalid authentication token |
| **403** | Forbidden | Authenticated but insufficient permissions |
| **404** | Not Found | Resource not found |
| **409** | Conflict | Duplicate resource (e.g., email already exists) |
| **422** | Unprocessable Entity | Valid syntax but semantic errors |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server-side error |
| **503** | Service Unavailable | Maintenance mode or overload |

### Error Codes

**Authentication Errors:**
- `AUTH_INVALID_CREDENTIALS` - Incorrect email/password
- `AUTH_TOKEN_EXPIRED` - Access token expired
- `AUTH_TOKEN_INVALID` - Malformed or invalid token
- `AUTH_EMAIL_NOT_VERIFIED` - Email verification required
- `AUTH_ACCOUNT_LOCKED` - Too many failed login attempts

**Validation Errors:**
- `VALIDATION_ERROR` - Input validation failed
- `MISSING_REQUIRED_FIELD` - Required field not provided
- `INVALID_FORMAT` - Field format is invalid

**Resource Errors:**
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `RESOURCE_ALREADY_EXISTS` - Duplicate resource creation
- `RESOURCE_CONFLICT` - Conflicting resource state

**Business Logic Errors:**
- `ASSESSMENT_ALREADY_STARTED` - Cannot start duplicate session
- `ASSESSMENT_ALREADY_COMPLETED` - Cannot modify completed assessment
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `BUDGET_EXCEEDED` - AI API budget exceeded

---

## Rate Limiting

### Rate Limits (Per IP Address)

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| **Authentication** | 5 requests | 15 minutes |
| **General API** | 100 requests | 15 minutes |
| **AI-Powered** | 10 requests | 1 minute |
| **Job Search** | 30 requests | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699012345
```

### Rate Limit Exceeded Response

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again in 15 minutes.",
    "retryAfter": 900
  }
}
```

---

## Endpoint Categories

### 1. Authentication & Users
- User registration, login, logout
- Profile management
- Password reset

### 2. Assessments
- Assessment catalog
- Taking assessments
- Viewing results

### 3. Learning Paths
- Personalized roadmaps
- Course recommendations
- Progress tracking

### 4. Jobs
- Job search and filtering
- Job recommendations
- Saved jobs

### 5. Notifications
- User notifications
- Notification preferences

### 6. Analytics (Admin)
- Platform metrics
- User engagement
- AI usage tracking

---

## Detailed Endpoints

---

## 1. Authentication & Users

### 1.1 Register User

**Endpoint:** `POST /api/v1/auth/register`

**Description:** Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "fullName": "John Doe",
  "userType": "learner"
}
```

**Validation Rules:**
- `email`: Valid email format, unique
- `password`: Minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 number
- `fullName`: 2-100 characters
- `userType`: `learner` or `jobseeker`

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "role": "user",
      "emailVerified": false
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 900
    }
  },
  "meta": {
    "message": "Registration successful. Please check your email to verify your account."
  }
}
```

**Error Responses:**
- `409 Conflict` - Email already exists
- `400 Bad Request` - Validation errors

---

### 1.2 Login

**Endpoint:** `POST /api/v1/auth/login`

**Description:** Authenticate user and receive tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "role": "user",
      "emailVerified": true,
      "profile": {
        "fullName": "John Doe",
        "avatarUrl": "https://cdn.skillpath.com/avatars/123.jpg"
      }
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 900
    }
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Email not verified or account locked
- `429 Too Many Requests` - Rate limit exceeded (5 attempts)

---

### 1.3 Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Description:** Get a new access token using refresh token.

**Request Body:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 900
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired refresh token

---

### 1.4 Logout

**Endpoint:** `POST /api/v1/auth/logout`

**Description:** Invalidate refresh token and log out user.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200):**
```json
{
  "success": true,
  "meta": {
    "message": "Logged out successfully"
  }
}
```

---

### 1.5 Forgot Password

**Endpoint:** `POST /api/v1/auth/forgot-password`

**Description:** Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "meta": {
    "message": "Password reset email sent. Please check your inbox."
  }
}
```

---

### 1.6 Reset Password

**Endpoint:** `POST /api/v1/auth/reset-password`

**Description:** Reset password using token from email.

**Request Body:**
```json
{
  "token": "abc123def456",
  "newPassword": "NewSecurePass123!"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "meta": {
    "message": "Password reset successful. Please log in with your new password."
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or expired token

---

### 1.7 Get Current User

**Endpoint:** `GET /api/v1/users/me`

**Description:** Get authenticated user's profile.

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "role": "user",
      "emailVerified": true,
      "createdAt": "2025-10-01T10:00:00Z",
      "profile": {
        "fullName": "John Doe",
        "phone": "+201234567890",
        "location": "Cairo, Egypt",
        "avatarUrl": "https://cdn.skillpath.com/avatars/123.jpg",
        "bio": "Aspiring full-stack developer",
        "linkedinUrl": "https://linkedin.com/in/johndoe",
        "githubUrl": "https://github.com/johndoe",
        "educationLevel": "Bachelor's Degree",
        "yearsOfExperience": 2,
        "currentJobTitle": "Junior Developer",
        "profileCompletionPercentage": 85
      },
      "preferences": {
        "userType": "jobseeker",
        "careerGoals": ["Full-Stack Developer", "DevOps Engineer"],
        "targetSkills": ["React", "Node.js", "Docker"],
        "learningPace": "moderate",
        "notificationEmail": true,
        "notificationInApp": true,
        "notificationFrequency": "daily",
        "language": "en",
        "timezone": "Africa/Cairo"
      },
      "skills": [
        {
          "skillId": 10,
          "skillName": "JavaScript",
          "proficiencyLevel": "intermediate",
          "proficiencyScore": 75,
          "verified": true
        },
        {
          "skillId": 15,
          "skillName": "React",
          "proficiencyLevel": "beginner",
          "proficiencyScore": 45,
          "verified": true
        }
      ]
    }
  }
}
```

---

### 1.8 Update User Profile

**Endpoint:** `PUT /api/v1/users/me`

**Description:** Update user profile information.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "profile": {
    "fullName": "John Doe",
    "phone": "+201234567890",
    "location": "Cairo, Egypt",
    "bio": "Aspiring full-stack developer",
    "linkedinUrl": "https://linkedin.com/in/johndoe",
    "githubUrl": "https://github.com/johndoe",
    "educationLevel": "Bachelor's Degree",
    "yearsOfExperience": 2,
    "currentJobTitle": "Junior Developer"
  }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "profile": {
      // Updated profile data
    }
  },
  "meta": {
    "message": "Profile updated successfully"
  }
}
```

---

### 1.9 Update User Preferences

**Endpoint:** `PUT /api/v1/users/me/preferences`

**Description:** Update user preferences and settings.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "userType": "jobseeker",
  "careerGoals": ["Full-Stack Developer", "DevOps Engineer"],
  "targetSkills": ["React", "Node.js", "Docker"],
  "learningPace": "fast",
  "notificationEmail": true,
  "notificationInApp": true,
  "notificationFrequency": "instant",
  "language": "en",
  "timezone": "Africa/Cairo"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "preferences": {
      // Updated preferences
    }
  }
}
```

---

### 1.10 Delete Account

**Endpoint:** `DELETE /api/v1/users/me`

**Description:** Soft delete user account (can be recovered).

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "password": "CurrentPassword123!",
  "reason": "No longer needed"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "meta": {
    "message": "Account deleted successfully. Your data will be retained for 30 days."
  }
}
```

---

## 2. Assessments

### 2.1 List Assessments

**Endpoint:** `GET /api/v1/assessments`

**Description:** Get list of available assessments.

**Query Parameters:**
- `skill` (optional): Filter by skill slug (e.g., `javascript`, `react`)
- `difficulty` (optional): Filter by difficulty (`easy`, `medium`, `hard`)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 50)

**Example:** `GET /api/v1/assessments?skill=javascript&difficulty=medium&page=1&limit=10`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "assessments": [
      {
        "id": 1,
        "title": "JavaScript Fundamentals Assessment",
        "slug": "javascript-fundamentals",
        "description": "Test your knowledge of JavaScript basics including variables, functions, and control flow.",
        "skill": {
          "id": 10,
          "name": "JavaScript",
          "category": "programming"
        },
        "difficulty": "medium",
        "questionCount": 20,
        "timeLimitMinutes": 30,
        "passingScore": 70,
        "isAdaptive": true,
        "tags": ["javascript", "fundamentals", "es6"],
        "stats": {
          "attemptCount": 1250,
          "averageScore": 72.5,
          "passRate": 68.2
        }
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalItems": 45,
      "itemsPerPage": 10
    }
  }
}
```

---

### 2.2 Get Assessment Details

**Endpoint:** `GET /api/v1/assessments/:id`

**Description:** Get detailed information about a specific assessment.

**Example:** `GET /api/v1/assessments/1`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "assessment": {
      "id": 1,
      "title": "JavaScript Fundamentals Assessment",
      "slug": "javascript-fundamentals",
      "description": "Comprehensive assessment covering JavaScript fundamentals...",
      "skill": {
        "id": 10,
        "name": "JavaScript",
        "category": "programming"
      },
      "difficulty": "medium",
      "questionCount": 20,
      "timeLimitMinutes": 30,
      "passingScore": 70,
      "isAdaptive": true,
      "questionTypes": [
        {"type": "mcq", "count": 10},
        {"type": "true_false", "count": 5},
        {"type": "code_completion", "count": 3},
        {"type": "short_answer", "count": 2}
      ],
      "tags": ["javascript", "fundamentals", "es6"],
      "prerequisites": ["Basic programming knowledge"],
      "stats": {
        "attemptCount": 1250,
        "averageScore": 72.5,
        "averageTimeMinutes": 25,
        "passRate": 68.2
      },
      "userAttempts": 0,
      "lastAttempt": null
    }
  }
}
```

---

### 2.3 Start Assessment

**Endpoint:** `POST /api/v1/assessments/:id/start`

**Description:** Start a new assessment session.

**Headers:** `Authorization: Bearer <access_token>`

**Example:** `POST /api/v1/assessments/1/start`

**Request Body:**
```json
{
  "settings": {
    "showExplanations": true
  }
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "session": {
      "id": 789,
      "assessmentId": 1,
      "status": "in_progress",
      "startedAt": "2025-11-04T10:30:00Z",
      "timeLimitMinutes": 30,
      "expiresAt": "2025-11-04T11:00:00Z",
      "currentQuestionIndex": 0,
      "totalQuestions": 20
    },
    "firstQuestion": {
      "id": 101,
      "type": "mcq",
      "questionText": "What is the output of console.log(typeof null)?",
      "options": [
        {"id": "a", "text": "null"},
        {"id": "b", "text": "object"},
        {"id": "c", "text": "undefined"},
        {"id": "d", "text": "number"}
      ],
      "points": 1,
      "timeEstimateSeconds": 60
    }
  }
}
```

**Error Responses:**
- `409 Conflict` - Assessment session already in progress
- `403 Forbidden` - Prerequisites not met

---

### 2.4 Get Current Question

**Endpoint:** `GET /api/v1/assessments/sessions/:sessionId/question`

**Description:** Get the current question in an active session.

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "question": {
      "id": 102,
      "type": "code_completion",
      "questionText": "Complete the function to reverse a string:",
      "codeTemplate": "function reverseString(str) {\n  // Your code here\n}",
      "points": 2,
      "timeEstimateSeconds": 180
    },
    "progress": {
      "currentQuestionIndex": 5,
      "totalQuestions": 20,
      "answeredQuestions": 4,
      "timeElapsedSeconds": 300
    }
  }
}
```

---

### 2.5 Submit Answer

**Endpoint:** `POST /api/v1/assessments/sessions/:sessionId/answers`

**Description:** Submit an answer for the current question.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body (MCQ):**
```json
{
  "questionId": 101,
  "answer": {
    "selectedOption": "b"
  },
  "timeTakenSeconds": 45
}
```

**Request Body (Code Completion):**
```json
{
  "questionId": 105,
  "answer": {
    "code": "function reverseString(str) {\n  return str.split('').reverse().join('');\n}"
  },
  "timeTakenSeconds": 180
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "result": {
      "isCorrect": true,
      "pointsEarned": 1,
      "explanation": "Correct! In JavaScript, typeof null returns 'object', which is a known quirk."
    },
    "nextQuestion": {
      "id": 102,
      "type": "true_false",
      "questionText": "JavaScript is a statically typed language.",
      "points": 1
    },
    "progress": {
      "currentQuestionIndex": 2,
      "totalQuestions": 20,
      "answeredQuestions": 1,
      "currentScore": 1,
      "timeElapsedSeconds": 45
    }
  }
}
```

---

### 2.6 Pause Assessment

**Endpoint:** `PUT /api/v1/assessments/sessions/:sessionId/pause`

**Description:** Pause an in-progress assessment.

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "session": {
      "id": 789,
      "status": "paused",
      "pausedAt": "2025-11-04T10:45:00Z"
    }
  },
  "meta": {
    "message": "Assessment paused. Note: Time will still be considered in your final score."
  }
}
```

---

### 2.7 Resume Assessment

**Endpoint:** `PUT /api/v1/assessments/sessions/:sessionId/resume`

**Description:** Resume a paused assessment.

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "session": {
      "id": 789,
      "status": "in_progress",
      "resumedAt": "2025-11-04T10:50:00Z"
    },
    "currentQuestion": {
      // Current question data
    }
  }
}
```

---

### 2.8 Complete Assessment

**Endpoint:** `POST /api/v1/assessments/sessions/:sessionId/complete`

**Description:** Mark assessment as completed and calculate final score.

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "result": {
      "id": 456,
      "sessionId": 789,
      "assessmentId": 1,
      "score": 15,
      "maxScore": 20,
      "percentage": 75.0,
      "timeTakenSeconds": 1800,
      "passed": true,
      "skillBreakdown": {
        "javascript-basics": 85,
        "functions": 70,
        "arrays": 80,
        "objects": 65
      },
      "skillGaps": [
        "Object destructuring",
        "Async/await patterns"
      ],
      "strengths": [
        "Array methods",
        "Function declarations"
      ],
      "recommendations": [
        "Focus on advanced object manipulation",
        "Practice async programming patterns"
      ],
      "completedAt": "2025-11-04T11:00:00Z"
    }
  },
  "meta": {
    "message": "Congratulations! You passed the assessment."
  }
}
```

---

### 2.9 Get Assessment Result

**Endpoint:** `GET /api/v1/assessments/results/:resultId`

**Description:** Get detailed results of a completed assessment.

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "result": {
      "id": 456,
      "assessment": {
        "id": 1,
        "title": "JavaScript Fundamentals Assessment"
      },
      "score": 15,
      "maxScore": 20,
      "percentage": 75.0,
      "timeTakenSeconds": 1800,
      "passed": true,
      "skillBreakdown": {
        "javascript-basics": 85,
        "functions": 70,
        "arrays": 80,
        "objects": 65
      },
      "questionResults": [
        {
          "questionId": 101,
          "type": "mcq",
          "questionText": "What is the output of console.log(typeof null)?",
          "userAnswer": "b",
          "correctAnswer": "b",
          "isCorrect": true,
          "pointsEarned": 1,
          "timeTakenSeconds": 45,
          "explanation": "In JavaScript, typeof null returns 'object'..."
        }
        // ... more questions
      ],
      "skillGaps": ["Object destructuring", "Async/await patterns"],
      "strengths": ["Array methods", "Function declarations"],
      "recommendations": [
        "Focus on advanced object manipulation",
        "Practice async programming patterns"
      ],
      "completedAt": "2025-11-04T11:00:00Z"
    }
  }
}
```

---

### 2.10 Get User Assessment History

**Endpoint:** `GET /api/v1/users/me/assessments`

**Description:** Get user's assessment attempt history.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `status` (optional): Filter by status (`completed`, `in_progress`, `abandoned`)
- `page`, `limit`: Pagination

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "attempts": [
      {
        "sessionId": 789,
        "assessment": {
          "id": 1,
          "title": "JavaScript Fundamentals Assessment",
          "skill": "JavaScript"
        },
        "status": "completed",
        "score": 15,
        "percentage": 75.0,
        "passed": true,
        "startedAt": "2025-11-04T10:30:00Z",
        "completedAt": "2025-11-04T11:00:00Z",
        "timeTakenSeconds": 1800
      }
    ],
    "stats": {
      "totalAttempts": 5,
      "completed": 4,
      "passed": 3,
      "averageScore": 72.5
    },
    "pagination": {
      "currentPage": 1,
      "totalPages": 1,
      "totalItems": 5
    }
  }
}
```

---

## 3. Learning Paths & Roadmaps

### 3.1 Get User Roadmap

**Endpoint:** `GET /api/v1/learning/roadmap`

**Description:** Get user's personalized learning roadmap.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `completed`, `archived`)

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "roadmap": {
      "id": 234,
      "title": "Full-Stack Web Developer Path",
      "description": "Personalized roadmap based on your JavaScript assessment",
      "targetSkill": {
        "id": 20,
        "name": "Full-Stack Development"
      },
      "estimatedDurationDays": 120,
      "status": "active",
      "progressPercentage": 35,
      "generatedBy": "ai",
      "createdAt": "2025-11-04T11:05:00Z",
      "items": [
        {
          "id": 501,
          "sequenceOrder": 1,
          "title": "Master JavaScript ES6+ Features",
          "description": "Deep dive into modern JavaScript syntax and features",
          "skill": {
            "id": 10,
            "name": "JavaScript"
          },
          "itemType": "course",
          "estimatedHours": 20,
          "status": "completed",
          "completedAt": "2025-11-10T15:30:00Z",
          "resources": [
            {
              "courseId": 10,
              "title": "JavaScript: The Advanced Concepts",
              "provider": "Udemy",
              "url": "https://udemy.com/course/advanced-javascript"
            }
          ]
        },
        {
          "id": 502,
          "sequenceOrder": 2,
          "title": "Build a Full-Stack Todo App",
          "description": "Apply your JavaScript skills to build a complete application",
          "itemType": "project",
          "estimatedHours": 15,
          "status": "in_progress",
          "resources": [
            {
              "type": "tutorial",
              "title": "Full-Stack Todo App Tutorial",
              "url": "https://..."
            }
          ]
        },
        {
          "id": 503,
          "sequenceOrder": 3,
          "title": "Learn React Fundamentals",
          "itemType": "course",
          "estimatedHours": 30,
          "status": "pending"
        }
      ]
    }
  }
}
```

---

### 3.2 Generate Roadmap

**Endpoint:** `POST /api/v1/learning/roadmap/generate`

**Description:** Generate a new personalized roadmap from assessment results.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "assessmentResultId": 456,
  "targetRole": "Full-Stack Developer",
  "timeCommitmentHoursPerWeek": 10,
  "learningPace": "moderate"
}
```

**Success Response (202):**
```json
{
  "success": true,
  "data": {
    "jobId": "roadmap-gen-abc123",
    "status": "processing",
    "estimatedCompletionSeconds": 10
  },
  "meta": {
    "message": "Roadmap generation started. You'll be notified when it's ready."
  }
}
```

**Poll Status:** `GET /api/v1/learning/roadmap/generate/:jobId`

**Completed Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "completed",
    "roadmap": {
      // Full roadmap data
    }
  }
}
```

---

### 3.3 Update Roadmap Item Status

**Endpoint:** `PUT /api/v1/learning/roadmap/items/:itemId`

**Description:** Update progress on a roadmap item.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "status": "completed",
  "notes": "Finished the course and built the project"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "item": {
      "id": 501,
      "status": "completed",
      "completedAt": "2025-11-10T15:30:00Z"
    },
    "roadmapProgress": {
      "totalItems": 10,
      "completedItems": 4,
      "progressPercentage": 40
    }
  }
}
```

---

### 3.4 Browse Courses

**Endpoint:** `GET /api/v1/learning/courses`

**Description:** Browse available learning courses.

**Query Parameters:**
- `skill` (optional): Filter by skill tag
- `difficulty` (optional): `beginner`, `intermediate`, `advanced`
- `provider` (optional): `Coursera`, `Udemy`, `YouTube`, etc.
- `isFree` (optional): `true` or `false`
- `search` (optional): Search query
- `page`, `limit`: Pagination

**Example:** `GET /api/v1/learning/courses?skill=react&difficulty=beginner&isFree=true`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "courses": [
      {
        "id": 10,
        "title": "React for Beginners",
        "slug": "react-for-beginners",
        "description": "Learn React from scratch with hands-on projects",
        "provider": "Udemy",
        "externalUrl": "https://udemy.com/course/react-beginners",
        "thumbnailUrl": "https://cdn.skillpath.com/courses/react.jpg",
        "difficulty": "beginner",
        "durationHours": 12,
        "language": "en",
        "priceEgp": 0,
        "skillTags": ["react", "javascript", "frontend"],
        "rating": 4.7,
        "enrollmentCount": 2500,
        "isFree": true
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 3,
      "totalItems": 28
    }
  }
}
```

---

### 3.5 Get Course Details

**Endpoint:** `GET /api/v1/learning/courses/:id`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "course": {
      "id": 10,
      "title": "React for Beginners",
      "description": "Comprehensive React course...",
      "provider": "Udemy",
      "externalUrl": "https://udemy.com/course/react-beginners",
      "thumbnailUrl": "https://cdn.skillpath.com/courses/react.jpg",
      "difficulty": "beginner",
      "durationHours": 12,
      "language": "en",
      "priceEgp": 0,
      "skillTags": ["react", "javascript", "frontend"],
      "rating": 4.7,
      "enrollmentCount": 2500,
      "isFree": true,
      "syllabus": [
        "Introduction to React",
        "Components and Props",
        "State and Lifecycle",
        "Hooks",
        "Building Projects"
      ],
      "userEnrolled": false
    }
  }
}
```

---

### 3.6 Enroll in Course

**Endpoint:** `POST /api/v1/learning/courses/:id/enroll`

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "roadmapItemId": 502
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "enrollment": {
      "id": 678,
      "courseId": 10,
      "enrollmentDate": "2025-11-04T12:00:00Z",
      "progressPercentage": 0,
      "status": "enrolled"
    }
  },
  "meta": {
    "message": "Successfully enrolled in course"
  }
}
```

---

### 3.7 Update Course Progress

**Endpoint:** `PUT /api/v1/learning/courses/:id/progress`

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "progressPercentage": 45,
  "timeSpentSeconds": 3600
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "enrollment": {
      "id": 678,
      "progressPercentage": 45,
      "status": "in_progress",
      "timeSpentSeconds": 3600,
      "lastAccessedAt": "2025-11-04T14:30:00Z"
    }
  }
}
```

---

## 4. Jobs

### 4.1 Search Jobs

**Endpoint:** `GET /api/v1/jobs`

**Description:** Search and filter job listings.

**Query Parameters:**
- `search` (optional): Search query (title, company, description)
- `location` (optional): Location filter
- `employmentType` (optional): `full_time`, `part_time`, `contract`, `internship`
- `experienceLevel` (optional): `entry`, `mid`, `senior`
- `skills` (optional): Comma-separated skill tags
- `salaryMin`, `salaryMax` (optional): Salary range in EGP
- `source` (optional): Job source (LinkedIn, Wuzzuf, etc.)
- `page`, `limit`: Pagination

**Example:** `GET /api/v1/jobs?location=Cairo&skills=javascript,react&experienceLevel=mid`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": 1001,
        "title": "Frontend Developer",
        "companyName": "Tech Innovations Egypt",
        "companyLogoUrl": "https://cdn.skillpath.com/companies/tech-innovations.jpg",
        "description": "We're looking for a talented Frontend Developer...",
        "location": "Cairo, Egypt",
        "employmentType": "full_time",
        "experienceLevel": "mid",
        "salaryMin": 15000,
        "salaryMax": 25000,
        "currency": "EGP",
        "requiredSkills": ["JavaScript", "React", "TypeScript", "CSS"],
        "niceToHaveSkills": ["Next.js", "GraphQL"],
        "source": "Wuzzuf",
        "externalUrl": "https://wuzzuf.net/jobs/...",
        "postedAt": "2025-11-01T10:00:00Z",
        "expiresAt": "2025-12-01T10:00:00Z",
        "isActive": true,
        "isSaved": false,
        "matchScore": 85
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 10,
      "totalItems": 95
    }
  }
}
```

---

### 4.2 Get Job Details

**Endpoint:** `GET /api/v1/jobs/:id`

**Headers:** `Authorization: Bearer <access_token>` (optional, for match score)

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 1001,
      "title": "Frontend Developer",
      "companyName": "Tech Innovations Egypt",
      "companyLogoUrl": "https://cdn.skillpath.com/companies/tech-innovations.jpg",
      "description": "Full job description...",
      "requirements": "• 3+ years of experience\n• Strong JavaScript skills\n...",
      "location": "Cairo, Egypt",
      "employmentType": "full_time",
      "experienceLevel": "mid",
      "salaryMin": 15000,
      "salaryMax": 25000,
      "currency": "EGP",
      "requiredSkills": ["JavaScript", "React", "TypeScript", "CSS"],
      "niceToHaveSkills": ["Next.js", "GraphQL"],
      "source": "Wuzzuf",
      "externalUrl": "https://wuzzuf.net/jobs/...",
      "postedAt": "2025-11-01T10:00:00Z",
      "expiresAt": "2025-12-01T10:00:00Z",
      "viewCount": 245,
      "applicationCount": 18,
      "isSaved": false,
      "matchScore": 85,
      "matchDetails": {
        "matchingSkills": ["JavaScript", "React", "CSS"],
        "missingSkills": ["TypeScript"],
        "recommendedActions": [
          "Complete TypeScript assessment to improve your match"
        ]
      }
    }
  }
}
```

---

### 4.3 Get Recommended Jobs

**Endpoint:** `GET /api/v1/jobs/recommended`

**Description:** Get AI-powered job recommendations based on user skills.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `limit` (optional): Number of recommendations (default: 20)

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        // Job data with matchScore
        "matchScore": 92,
        "matchReason": "Your JavaScript and React skills are a great fit"
      }
    ]
  }
}
```

---

### 4.4 Save Job

**Endpoint:** `POST /api/v1/jobs/:id/save`

**Description:** Bookmark a job for later.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "notes": "Interesting opportunity, apply next week"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "savedJob": {
      "id": 789,
      "jobId": 1001,
      "savedAt": "2025-11-04T15:00:00Z",
      "notes": "Interesting opportunity, apply next week"
    }
  }
}
```

---

### 4.5 Get Saved Jobs

**Endpoint:** `GET /api/v1/jobs/saved`

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "savedJobs": [
      {
        "id": 789,
        "job": {
          // Full job data
        },
        "savedAt": "2025-11-04T15:00:00Z",
        "notes": "Interesting opportunity, apply next week"
      }
    ]
  }
}
```

---

### 4.6 Unsave Job

**Endpoint:** `DELETE /api/v1/jobs/:id/save`

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "meta": {
    "message": "Job removed from saved list"
  }
}
```

---

## 5. Notifications

### 5.1 Get Notifications

**Endpoint:** `GET /api/v1/notifications`

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `read` (optional): `true` or `false` to filter
- `type` (optional): Filter by notification type
- `page`, `limit`: Pagination

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": 5001,
        "type": "ROADMAP_READY",
        "title": "Your Learning Roadmap is Ready!",
        "message": "We've created a personalized learning path based on your JavaScript assessment.",
        "actionUrl": "/learning/roadmap",
        "priority": "high",
        "read": false,
        "createdAt": "2025-11-04T11:10:00Z"
      },
      {
        "id": 5002,
        "type": "NEW_JOB_MATCH",
        "title": "5 New Jobs Match Your Skills",
        "message": "Check out these exciting opportunities for React developers.",
        "actionUrl": "/jobs/recommended",
        "priority": "normal",
        "read": false,
        "createdAt": "2025-11-04T09:00:00Z"
      }
    ],
    "unreadCount": 3,
    "pagination": {
      "currentPage": 1,
      "totalPages": 2,
      "totalItems": 15
    }
  }
}
```

---

### 5.2 Mark Notification as Read

**Endpoint:** `PUT /api/v1/notifications/:id/read`

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "notification": {
      "id": 5001,
      "read": true,
      "readAt": "2025-11-04T16:00:00Z"
    }
  }
}
```

---

### 5.3 Mark All as Read

**Endpoint:** `PUT /api/v1/notifications/read-all`

**Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "success": true,
  "meta": {
    "message": "All notifications marked as read",
    "count": 3
  }
}
```

---

### 5.4 Update Notification Preferences

**Endpoint:** `PUT /api/v1/notifications/preferences`

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "emailEnabled": true,
  "inAppEnabled": true,
  "frequency": "daily",
  "types": {
    "ROADMAP_READY": true,
    "ASSESSMENT_REMINDER": true,
    "NEW_JOB_MATCH": true,
    "COURSE_PROGRESS": false,
    "STREAK_REMINDER": true,
    "WEEKLY_DIGEST": true
  }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "preferences": {
      // Updated preferences
    }
  }
}
```

---

## 6. Analytics (Admin Only)

### 6.1 Get Platform Dashboard

**Endpoint:** `GET /api/v1/analytics/dashboard`

**Headers:** `Authorization: Bearer <access_token>` (requires `admin` role)

**Query Parameters:**
- `startDate`, `endDate`: Date range

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "overview": {
      "totalUsers": 5240,
      "activeUsers": 1250,
      "totalAssessments": 8450,
      "totalRoadmaps": 3120,
      "totalJobViews": 15230
    },
    "userGrowth": [
      {"date": "2025-11-01", "newUsers": 45, "activeUsers": 1200},
      {"date": "2025-11-02", "newUsers": 52, "activeUsers": 1220}
    ],
    "assessmentStats": {
      "totalAttempts": 12340,
      "averageScore": 72.5,
      "passRate": 68.2,
      "mostPopular": [
        {"id": 1, "title": "JavaScript Fundamentals", "attempts": 1250}
      ]
    },
    "aiUsage": {
      "totalTokens": 1250000,
      "totalCostUsd": 45.50,
      "byService": {
        "question_generation": {"tokens": 500000, "cost": 18.20},
        "roadmap_generation": {"tokens": 750000, "cost": 27.30}
      }
    }
  }
}
```

---

## Webhook Events (Future)

For real-time updates, webhooks will be implemented for:

- `assessment.completed` - User completed an assessment
- `roadmap.generated` - Roadmap generation finished
- `job.matched` - New high-match job found for user
- `payment.success` - Payment processed (future)

---

## SDK / Client Libraries (Future)

Official SDKs planned for:
- JavaScript/TypeScript
- Python
- Mobile (React Native)

---

**API Specification Document Prepared By:** SkillPath AI Development Team
**Version:** 1.0 (MVP)
**OpenAPI/Swagger:** Available at `/api/v1/docs`
