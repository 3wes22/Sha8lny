# Sha8alny Backend - Context for Development

## Project Overview
AI-powered career development platform for Egypt. Microservices architecture with Django + PostgreSQL.

## Architecture
- 9 Microservices: User, Assessment, Roadmap, Course, Job, Progress, Career Tools, Notification, Community
- See: docs/ARCHITECTURE.md for complete service design
- Each service has: models.py, serializers.py, views.py, services.py, tasks.py

## Database
- PostgreSQL with UUID primary keys (not integers!)
- Every table has: created_at, updated_at, is_deleted, deleted_at
- See: docs/DATABASE_SCHEMA.md for all 30+ tables
- CRITICAL: Always check DATABASE_SCHEMA.md before creating models

## Code Standards
- Functions: snake_case
- Classes: PascalCase
- Type hints: Always required
- Docstrings: Google-style required
- See: docs/CODING_STANDARDS.md for complete standards

## Key Rules
1. Always use UUID for primary keys
2. Business logic goes in services.py (NOT views.py)
3. Use select_related/prefetch_related for relationships
4. Follow patterns in ARCHITECTURE.md
5. Check DATABASE_SCHEMA.md for exact field names/types

## Reference Documents
- Architecture: docs/ARCHITECTURE.md
- Database: docs/DATABASE_SCHEMA.md
- Standards: docs/CODING_STANDARDS.md
- Tech Stack: docs/TECH_STACK.md
```

---

## Step 3: Add a .clauignore File (1 minute)

**Create: `.clauignore` in project root**

Tell Claude Code what to ignore:
```
# Virtual environment
venv/
env/
.venv/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Database
*.sqlite3
db.sqlite3

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# Large files
node_modules/
staticfiles/
media/
```

---

## Step 4: Configure Claude Code Settings (2 minutes)

**In VS Code:**

1. Open Command Palette: `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type: "Claude Code: Settings"
3. Configure:
   - **Model**: Claude Sonnet 4.5 (best for coding)
   - **Context files**: Point to `.claudecode/context.md`

---

## Step 5: How to Give Context When Starting a Task

### When Starting ANY New Feature:

**Use this template in Claude Code chat:**
```
I'm implementing [SERVICE_NAME] Service for Sha8alny.

Context:
1. Check docs/ARCHITECTURE.md → [SERVICE_NAME] Service section
2. Check docs/DATABASE_SCHEMA.md → [SERVICE_NAME] tables
3. Follow docs/CODING_STANDARDS.md

Task: [Specific task, e.g., "Create User model"]

Requirements:
- Use UUID primary keys
- Include audit fields (created_at, updated_at, is_deleted, deleted_at)
- Follow exact field names from DATABASE_SCHEMA.md
- Add type hints and docstrings
```

---

## Step 6: Reference Specific Documentation Sections

### For Models:
```
Create the Assessment model.

CRITICAL: 
1. Open docs/DATABASE_SCHEMA.md
2. Find "assessments" table (line ~XXX)
3. Use EXACT field names and types from the schema
4. Include all constraints shown
5. Follow the model pattern from CODING_STANDARDS.md
```

### For APIs:
```
Create Assessment API endpoints.

Reference:
1. docs/ARCHITECTURE.md → Assessment Service → API Endpoints section
2. Use the REST patterns defined there
3. Follow DRF best practices from CODING_STANDARDS.md
```

### For Service Logic:
```
Implement assessment question generation logic.

Context:
1. docs/ARCHITECTURE.md → Assessment Service → Business Logic
2. This should be in services.py (NOT views.py)
3. Will call LLM APIs (OpenAI/Anthropic)
4. Should be async (Celery task)
```

---

## Step 7: Best Practices for Claude Code Prompts

### ✅ GOOD Prompts:

**Specific + References Documentation:**
```
Create the User model following docs/DATABASE_SCHEMA.md exactly.
The table is called "users" and has these fields: [list if you want]
Use UUID primary key and include all audit fields.
```

**Includes Architecture Context:**
```
Implement the roadmap generation service.
According to docs/ARCHITECTURE.md, this should:
- Be in RoadmapService class
- Call AI model for generation
- Run as Celery background task
- Return roadmap structure
```

**Specifies Standards:**
```
Create serializers for Assessment model.
Follow docs/CODING_STANDARDS.md:
- Use type hints
- Add docstrings
- Nested serialization for relationships
```

### ❌ BAD Prompts:

**Too Vague:**
```
Create a user model
```
*(Claude doesn't know your schema!)*

**No Context:**
```
Make an API for assessments
```
*(Claude doesn't know your architecture!)*

**Assumes Knowledge:**
```
Do it like we discussed
```
*(Claude Code doesn't have conversation memory!)*

---

## Step 8: Working with Multiple Files

### When Claude Code Needs Multiple Files:

**Tell it explicitly:**
```
I need to create the complete User Service.

Files needed:
1. apps/users/models.py - From docs/DATABASE_SCHEMA.md
2. apps/users/serializers.py - DRF serializers
3. apps/users/views.py - ViewSets
4. apps/users/services.py - Business logic
5. apps/users/urls.py - URL routing

Start with models.py first, following DATABASE_SCHEMA.md exactly.
```

---

## Step 9: Iterative Development Pattern

### Follow This Pattern for Each Feature:

**1. Give Context:**
```
Working on Assessment Service.
Refs: docs/ARCHITECTURE.md (Assessment section), docs/DATABASE_SCHEMA.md (assessments table)
```

**2. Start with Models:**
```
Create Assessment model from DATABASE_SCHEMA.md.
EXACT field names, types, constraints.
```

**3. Then Serializers:**
```
Create AssessmentSerializer.
Handle JSONB fields (questions, user_responses).
```

**4. Then Views:**
```
Create AssessmentViewSet.
Endpoints per ARCHITECTURE.md.
```

**5. Add Service Layer:**
```
Create AssessmentService class.
Business logic for question generation.
```

**6. Add Celery Tasks:**
```
Create Celery task for async processing.
```

---

## Step 10: Quick Reference Card

**Keep this open while coding:**

### Before Every Task, Ask:
1. ✅ Which service am I working on?
2. ✅ What does ARCHITECTURE.md say about this?
3. ✅ What does DATABASE_SCHEMA.md say about the tables?
4. ✅ What patterns does CODING_STANDARDS.md require?

### In Every Claude Code Prompt, Include:
1. 📁 File path you're working on
2. 📖 Reference to relevant doc section
3. 🎯 Specific task
4. ✅ Key requirements (UUID, audit fields, etc.)

---

## Example: First Complete Task

### Creating User Service - Complete Prompt:
```
I'm creating the User Service for Sha8alny.

CONTEXT:
- Check docs/DATABASE_SCHEMA.md → User Service Schema
- Check docs/ARCHITECTURE.md → User Service section
- Follow docs/CODING_STANDARDS.md → Django Model structure

TASK: Create apps/users/models.py

REQUIREMENTS:
1. Create 4 models: User, Skill, UserSkill, UserPreferences
2. Use EXACT field names from DATABASE_SCHEMA.md
3. UUID primary keys (not auto-increment)
4. Audit fields on ALL tables: created_at, updated_at, is_deleted, deleted_at
5. Add Meta class with db_table, ordering, indexes
6. Add __str__ and __repr__ methods
7. Type hints and Google-style docstrings

Start with the User model. Use the exact structure from DATABASE_SCHEMA.md line 234.
```

---

## 🎯 Summary: Your Workflow

### Setup (One-Time):
1. ✅ Create `/docs` folder with 6 key files
2. ✅ Create `.claudecode/context.md`
3. ✅ Create `.clauignore`
4. ✅ Configure Claude Code settings

### Every Task (Repeat):
1. **Identify** which service/feature
2. **Reference** relevant docs sections
3. **Prompt** Claude Code with context + task + requirements
4. **Review** generated code against documentation
5. **Test** the code
6. **Iterate** if needed

---

## 🚀 Ready to Start?

**First Task Template:**
```
Starting Sha8alny backend implementation.

First service: User Service

Task: Create apps/users/models.py

Context:
- docs/DATABASE_SCHEMA.md → User Service Schema → users table
- UUID primary key required
- Audit fields required on all models
- Follow model structure from docs/CODING_STANDARDS.md

Create the User model with ALL fields from the schema.
Use exact field names and types.