
---

# Sha8lny – AI-Powered Career Empowerment Platform

## 1. Project Overview

Sha8lny is an intelligent platform designed to bridge the gap between students, graduates, and the job market.
The system provides personalized career guidance through AI-driven assessments, adaptive learning pathways, and integration with local industry data.

The platform's primary objective is to help users identify their strengths, develop relevant skills, and connect with suitable job opportunities in the Egyptian market.

---

## 2. Project Vision

To empower students and young professionals in Egypt with data-driven insights, personalized learning paths, and real-time market information, enabling them to make informed career decisions and improve employability.

---

## 3. Key Features

1. **Intelligent Career Assessment**
   AI-powered evaluation combining:

   * Technical skills testing
   * Soft skills and personality profiling
   * Personalized career recommendations

2. **Dynamic Learning Pathways**
   Automatically updated learning curricula that adapt based on:

   * Market trends
   * Individual progress and interests
   * Job role evolution

3. **Local Market Integration**
   Real-time access to:

   * Salary benchmarking
   * Company culture and skills demand
   * Industry-specific requirements

4. **Gamified Learning Experience**

   * Progress tracking and achievements
   * Peer competition features
   * Motivation through rewards and milestones

5. **Corporate Partnership Network**
   Direct collaboration with Egyptian companies for:

   * Internships
   * Graduation projects
   * Job placements

6. **Certification and Credentialing**
   Industry-recognized certificates validated by local professional bodies and institutions.

---

## 4. Project Structure

```
Sha8lny/
├── Backend/                # Django REST API (Python)
│   ├── apps/
│   │   ├── users/         # User authentication & profiles
│   │   ├── courses/       # Learning content management
│   │   ├── assessments/   # Skills assessment system
│   │   ├── roadmaps/      # Career path generation
│   │   ├── progress/      # User progress tracking
│   │   ├── jobs/          # Job listings & matching
│   │   ├── advisory/      # AI career advisor
│   │   ├── career_tools/  # Resume builder, etc.
│   │   └── notifications/ # User notifications
│   ├── config/            # Django settings
│   └── requirements.txt
│
├── Frontend/              # React + Vite + TypeScript
│   ├── src/
│   │   ├── pages/        # 14 pages (Dashboard, Jobs, etc.)
│   │   ├── components/   # Reusable UI components
│   │   └── hooks/        # Custom React hooks
│   ├── package.json
│   └── FRONTEND_INTEGRATION.md  # API integration guide
│
├── ai-models/             # ML/AI Infrastructure (Python)
│   ├── src/
│   │   ├── llm/          # Language model inference
│   │   ├── rag/          # Retrieval Augmented Generation
│   │   └── recommendations/  # Recommendation engine
│   └── requirements.txt
│
├── docs/                  # Documentation
│   ├── SRS.md            # Software Requirements Specification
│   ├── DATABASE_SCHEMA.md
│   ├── ARCHITECTURE.md
│   ├── ERD.svg           # Entity Relationship Diagram
│   └── TECH_STACK.md
│
├── CLAUDE.md             # AI assistant instructions
└── README.md             # This file
```

---

## 5. Tech Stack

| Layer           | Technologies                          |
| --------------- | ------------------------------------- |
| Frontend        | React 18, Vite, TypeScript, TailwindCSS, shadcn/ui |
| Backend         | Django 5.x, Django REST Framework     |
| Database        | PostgreSQL                            |
| AI/ML           | Python, PyTorch, LangChain            |
| Deployment      | Docker, AWS / Vercel                  |
| Version Control | Git & GitHub                          |

---

## 6. Getting Started

### Backend Setup

```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure environment variables
python manage.py migrate
python manage.py runserver
```

### Frontend Setup

```bash
cd Frontend
npm install
npm run dev               # Runs on http://localhost:5173
```

### AI Models Setup

```bash
cd ai-models
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 7. Team Members

| Name          | Role               | Responsibility                               |
| ------------- | ------------------ | -------------------------------------------- |
| Mahmoud Ahmed | Team Leader        | Project coordination, architecture design    |
| [Member 2]    | Backend Developer  | API and database implementation              |
| [Member 3]    | Frontend Developer | UI/UX and React development                  |
| [Member 4]    | AI/ML Engineer     | Career assessment and recommendation systems |
| [Member 5]    | Documentation & QA | Reports, testing, and quality assurance      |

---

## 8. Project Milestones

| Milestone | Description                                | Status      |
| --------- | ------------------------------------------ | ----------- |
| 0         | Project setup, repository creation         | ✅ Completed |
| 1         | Requirements analysis (SRS)                | ✅ Completed |
| 2         | System design (ERD, Architecture)          | ✅ Completed |
| 3         | Backend API development                    | ✅ Completed |
| 4         | Frontend UI development                    | ✅ Completed |
| 5         | AI/ML infrastructure setup                 | ✅ Completed |
| 6         | Frontend-Backend integration               | 🔄 In Progress |
| 7         | Testing and deployment                     | Pending     |
| 8         | Final documentation and presentation       | Pending     |

---

## 9. Documentation

- **API Integration**: See `Frontend/FRONTEND_INTEGRATION.md`
- **Database Schema**: See `docs/DATABASE_SCHEMA.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Requirements**: See `docs/SRS.md`

---

## 10. License

This project is developed for the **Nile University Graduation Project (ITCS Department, 2025)**.
All rights reserved © Team Sha8lny.

---
