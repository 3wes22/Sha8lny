# AI Models Planning Document
## Sha8alny - AI-Powered Career Development Platform

**Branch:** ai-models
**Status:** Planning Phase
**Date:** December 2024

---

## Table of Contents
1. [Overview](#overview)
2. [AI Components](#ai-components)
3. [Implementation Roadmap](#implementation-roadmap)
4. [Technical Requirements](#technical-requirements)
5. [Development Tasks](#development-tasks)

---

## Overview

This document outlines the planning and implementation strategy for all AI components in the Sha8alny platform. Based on the SRS requirements, we need to build four major AI-powered features:

1. **AI Skill Assessment System** - Question generation and evaluation
2. **Learning Roadmap Generator** - Personalized learning path creation
3. **RAG Career Advisory System** - Conversational career guidance
4. **Job Recommendation Engine** - Intelligent job matching

---

## AI Components

### 1. AI Skill Assessment System

#### Purpose
Generate personalized assessment questionnaires and evaluate user responses to identify skill levels, strengths, and gaps.

#### Key Features
- **Question Generation** (FR-006)
  - Generate 20-25 customized questions per assessment
  - Question types: Multiple choice (60%), Scenario-based (30%), Self-assessment (10%)
  - Difficulty levels: Beginner to Advanced
  - Skills covered: Technical + Transferable professional skills

- **Response Evaluation** (FR-008)
  - Analyze user responses using LLM
  - Produce proficiency levels: Beginner, Intermediate, Advanced
  - Score individual skill categories (0-100 scale)
  - Identify strengths and skill gaps
  - Generate development recommendations

#### Technical Approach
```
User Profile + Career Path → LLM Prompt → Generated Questions
User Responses + Questions → LLM Evaluation → Skill Analysis Report
```

#### LLM Requirements
- **Model:** GPT-4 or Claude (Anthropic)
- **Max Time:** 30 seconds for generation, 45 seconds for evaluation
- **Retry Logic:** 3 attempts with exponential backoff
- **Async Processing:** Background task queue (Celery)

---

### 2. Learning Roadmap Generator

#### Purpose
Create customized, sequential learning paths based on assessment results and user preferences.

#### Key Features
- **Roadmap Structure** (FR-011)
  - Hierarchical organization: Phases → Milestones → Skills
  - Minimum 2 phases, 3 milestones per phase, 2 skills per milestone
  - Realistic time estimates based on user's available hours
  - Prerequisites identified for proper sequencing

- **Customization** (FR-013)
  - User preferences: timeframe, hours/week, learning formats, budget
  - Manual milestone addition/removal/reordering
  - Editable durations and descriptions

#### Technical Approach
```
Assessment Results + User Preferences → LLM Prompt → Structured Roadmap
Roadmap Data → Database Storage → Interactive Visualization
```

#### LLM Requirements
- **Model:** GPT-4 or Claude
- **Max Time:** 60 seconds
- **Output Format:** Structured JSON with phases, milestones, skills
- **Validation:** Ensure minimum structure requirements met

---

### 3. RAG Career Advisory System

#### Purpose
Provide context-aware career guidance through conversational interface using retrieval-augmented generation.

#### Key Features
- **Knowledge Base Management** (FR-015)
  - Curated content: career paths, skills, industry trends, resources
  - Document processing: chunking (500-1000 chars), embedding generation
  - Metadata: title, tags, timestamps, source attribution

- **Question Processing** (FR-016)
  - Convert questions to vector embeddings
  - Retrieve top 5 relevant chunks (cosine similarity > 0.7)
  - Generate contextual answers (200-400 words)
  - Include source citations

- **Conversation Context** (FR-017)
  - Maintain previous 3 exchanges for continuity
  - Handle follow-up questions with pronouns
  - Conversation history limit: 20 exchanges

#### Technical Approach
```
Knowledge Base Documents → Chunking → Embeddings → Vector Database

User Question → Embedding → Vector Search → Relevant Chunks
Chunks + Question + Context → LLM Prompt → Answer + Citations
```

#### Technical Stack
- **Vector Database:** Pinecone, ChromaDB, or Qdrant
- **Embedding Model:** 384-dim or 1536-dim vectors
- **LLM:** GPT-4 or Claude
- **Max Response Time:** 10 seconds
- **Similarity Metric:** Cosine similarity

---

### 4. Job Recommendation Engine

#### Purpose
Match users with relevant job opportunities based on their skills, experience, and career goals.

#### Key Features
- **Recommendation Algorithm** (FR-021)
  - Match score calculation based on:
    - Skill overlap between user profile and job requirements
    - Experience level alignment
    - Career path relevance
  - Rank by match score (descending)
  - Display top 10 recommendations
  - Show match percentage (e.g., "85% match")

- **Explainability** (FR-021.7)
  - "Why this job?" feature showing:
    - Matching skills
    - Career goal alignment
    - Experience level fit

#### Technical Approach
```
User Profile + Job Postings → Matching Algorithm → Ranked Recommendations
Matching Skills + Career Goals → Explainability Logic → "Why this job?" Details
```

#### Algorithm Design
- Skill matching weight: 50%
- Experience level weight: 30%
- Career path alignment weight: 20%
- Exclude already-applied jobs
- Update daily with new job postings

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Set up infrastructure and basic LLM integration

**Tasks:**
1. Set up LLM API clients (OpenAI GPT-4, Anthropic Claude)
2. Implement retry logic and error handling
3. Create prompt templates for each AI component
4. Set up async task processing (Celery + Redis)
5. Implement basic logging and monitoring

**Deliverables:**
- LLM service wrapper classes
- Prompt template library
- Celery task queue configured
- Basic error handling and logging

---

### Phase 2: AI Skill Assessment (Weeks 2-3)
**Goal:** Build question generation and evaluation system

**Tasks:**
1. Design question generation prompts
2. Implement question generation service
3. Create question presentation UI
4. Design evaluation prompts
5. Implement response evaluation service
6. Build results visualization

**Deliverables:**
- Question generation endpoint
- Evaluation endpoint
- Assessment UI components
- Results display page

**Testing:**
- Generate assessments for 5 different career paths
- Validate question quality and variety
- Test evaluation accuracy against sample responses
- Performance testing (30s generation, 45s evaluation limits)

---

### Phase 3: Learning Roadmap Generator (Week 4)
**Goal:** Create personalized roadmap generation

**Tasks:**
1. Design roadmap generation prompts
2. Implement roadmap generation service
3. Create database schema for roadmaps
4. Build roadmap visualization UI
5. Implement customization features (add/edit/delete milestones)
6. Integrate with assessment results

**Deliverables:**
- Roadmap generation endpoint
- Roadmap database models
- Interactive roadmap visualization
- Customization UI

**Testing:**
- Generate roadmaps with different parameters
- Validate hierarchical structure (phases/milestones/skills)
- Test time estimation accuracy
- User acceptance testing for customization features

---

### Phase 4: RAG Career Advisory System (Weeks 5-6)
**Goal:** Build conversational career advisory with RAG

**Tasks:**

**Week 5: Knowledge Base & Vector Database**
1. Set up vector database (Pinecone/ChromaDB/Qdrant)
2. Create knowledge base content structure
3. Implement document chunking pipeline
4. Implement embedding generation
5. Build vector storage and indexing
6. Create knowledge base management admin UI

**Week 6: Conversational Interface**
7. Design RAG prompt templates
8. Implement question embedding generation
9. Build vector similarity search
10. Implement context retrieval logic
11. Create response generation service
12. Build conversational UI with chat interface
13. Implement conversation history management
14. Add citation display

**Deliverables:**
- Vector database integration
- Knowledge base processing pipeline
- Admin UI for KB management
- Conversational advisory endpoint
- Chat interface UI
- Context management system

**Testing:**
- Populate KB with sample career content
- Test retrieval accuracy (precision/recall)
- Evaluate response quality and relevance
- Test conversation continuity with follow-ups
- Performance testing (10s response time limit)
- Load test vector database queries

---

### Phase 5: Job Recommendation Engine (Week 7)
**Goal:** Build intelligent job matching system

**Tasks:**
1. Design matching algorithm
2. Implement skill overlap calculation
3. Implement experience level scoring
4. Implement career path alignment scoring
5. Build composite match score calculation
6. Create recommendation ranking logic
7. Build "Why this job?" explainability
8. Integrate with job search UI
9. Implement feedback collection

**Deliverables:**
- Job recommendation endpoint
- Matching algorithm implementation
- Recommendation UI components
- Explainability feature

**Testing:**
- Test with diverse user profiles
- Validate recommendation accuracy
- A/B test different weight configurations
- Collect user feedback on recommendations
- Performance testing (daily batch processing)

---

### Phase 6: Integration & Optimization (Week 8)
**Goal:** Integrate all components, optimize performance, prepare for deployment

**Tasks:**
1. End-to-end integration testing
2. Performance optimization (caching, query optimization)
3. LLM cost optimization (prompt engineering, caching)
4. Comprehensive error handling
5. Monitoring and alerting setup
6. Documentation completion
7. User acceptance testing
8. Deployment preparation

**Deliverables:**
- Fully integrated system
- Performance benchmarks met
- Monitoring dashboards
- Complete technical documentation
- User documentation
- Deployment scripts

---

## Technical Requirements

### LLM APIs

#### OpenAI GPT-4 (Primary)
- **API Key:** Environment variable `OPENAI_API_KEY`
- **Model:** `gpt-4-turbo` or `gpt-4`
- **Rate Limits:** 10,000 tokens/minute (consider scaling)
- **Cost Consideration:** ~$0.03/1K tokens (input), ~$0.06/1K tokens (output)
- **Use Cases:** Assessment generation/evaluation, Roadmap generation, RAG responses

#### Anthropic Claude (Fallback)
- **API Key:** Environment variable `ANTHROPIC_API_KEY`
- **Model:** `claude-3-opus` or `claude-3-sonnet`
- **Use Cases:** Backup when OpenAI unavailable
- **Prompt Format:** Different from OpenAI (prompt string vs messages array)

### Vector Database

#### Options Evaluation
1. **Pinecone** (Cloud-hosted)
   - Pros: Managed service, excellent performance, easy scaling
   - Cons: Cost at scale, vendor lock-in
   - Free tier: 1M vectors

2. **ChromaDB** (Self-hosted or cloud)
   - Pros: Open-source, flexible, good for MVP
   - Cons: Self-hosting complexity for production
   - Best for: Development and MVP

3. **Qdrant** (Self-hosted or cloud)
   - Pros: Open-source, high performance, good filtering
   - Cons: Self-hosting maintenance
   - Best for: Production if self-hosting

**Recommendation for MVP:** ChromaDB (simplicity, free, good for development)
**Recommendation for Production:** Pinecone or Qdrant based on scale needs

### Embedding Models

#### OpenAI Embeddings
- **Model:** `text-embedding-3-small` (1536 dimensions)
- **Cost:** $0.02/1M tokens
- **Performance:** High quality, fast
- **Use Case:** RAG system embeddings

#### Alternative: Sentence Transformers (Open-source)
- **Model:** `all-MiniLM-L6-v2` (384 dimensions)
- **Cost:** Free (self-hosted)
- **Performance:** Good for many use cases
- **Use Case:** Cost-sensitive deployments

### Infrastructure

#### Async Task Queue
- **Tool:** Celery
- **Broker:** Redis
- **Workers:** 2-4 workers for MVP
- **Tasks:** Question generation, evaluation, roadmap generation, embedding creation

#### Caching
- **Tool:** Redis
- **Cache Items:**
  - LLM responses for common queries (TTL: 24 hours)
  - User profile data (TTL: 1 hour)
  - Job listings (TTL: 24 hours)
  - Knowledge base embeddings (indefinite until content update)

#### Database
- **Primary:** PostgreSQL 13+
- **Vector Storage:** Separate vector database (ChromaDB/Pinecone/Qdrant)
- **Schema:** User profiles, assessments, roadmaps, conversation history, jobs

---

## Development Tasks

### Directory Structure
```
ai-models/
├── assessment/
│   ├── __init__.py
│   ├── question_generator.py
│   ├── evaluator.py
│   ├── prompts.py
│   └── models.py
├── roadmap/
│   ├── __init__.py
│   ├── generator.py
│   ├── prompts.py
│   └── models.py
├── rag/
│   ├── __init__.py
│   ├── knowledge_base.py
│   ├── embeddings.py
│   ├── retriever.py
│   ├── response_generator.py
│   ├── prompts.py
│   └── models.py
├── recommendations/
│   ├── __init__.py
│   ├── matcher.py
│   ├── ranker.py
│   ├── explainer.py
│   └── models.py
├── llm/
│   ├── __init__.py
│   ├── client.py
│   ├── openai_client.py
│   ├── anthropic_client.py
│   └── retry_handler.py
├── utils/
│   ├── __init__.py
│   ├── validators.py
│   ├── parsers.py
│   └── logging.py
└── tests/
    ├── test_assessment.py
    ├── test_roadmap.py
    ├── test_rag.py
    └── test_recommendations.py
```

### Core Tasks Checklist

#### Foundation
- [ ] Set up Python project structure
- [ ] Install dependencies (openai, anthropic, celery, redis, chromadb, etc.)
- [ ] Create LLM client wrapper with retry logic
- [ ] Implement async task queue
- [ ] Set up logging and monitoring
- [ ] Create prompt template system
- [ ] Implement error handling patterns

#### AI Assessment
- [ ] Design question generation prompts
- [ ] Implement QuestionGenerator class
- [ ] Create question validation logic
- [ ] Design evaluation prompts
- [ ] Implement AssessmentEvaluator class
- [ ] Create result parsing and structuring
- [ ] Build API endpoints
- [ ] Write unit tests
- [ ] Performance testing

#### Roadmap Generator
- [ ] Design roadmap generation prompts
- [ ] Implement RoadmapGenerator class
- [ ] Create roadmap validation logic
- [ ] Implement database models
- [ ] Build customization features
- [ ] Create API endpoints
- [ ] Write unit tests
- [ ] Integration testing with assessment

#### RAG System
- [ ] Set up vector database
- [ ] Implement document chunking
- [ ] Create embedding generation pipeline
- [ ] Build vector storage and indexing
- [ ] Implement similarity search
- [ ] Design RAG prompts
- [ ] Create ResponseGenerator class
- [ ] Implement conversation context management
- [ ] Build knowledge base admin UI
- [ ] Create chat API endpoints
- [ ] Write unit and integration tests
- [ ] Load testing

#### Job Recommendations
- [ ] Design matching algorithm
- [ ] Implement skill matching logic
- [ ] Create experience level scoring
- [ ] Build career path alignment scoring
- [ ] Implement composite scoring
- [ ] Create ranking algorithm
- [ ] Build explainability feature
- [ ] Create API endpoints
- [ ] Write unit tests
- [ ] A/B testing framework

#### Integration & Deployment
- [ ] End-to-end integration testing
- [ ] Performance optimization
- [ ] Cost optimization (caching, prompt engineering)
- [ ] Monitoring setup (metrics, alerts)
- [ ] Documentation (API docs, user guides, technical docs)
- [ ] Deployment scripts
- [ ] Security review
- [ ] Load testing
- [ ] User acceptance testing

---

## Next Steps

1. **Review and Refine:** Review this plan with the team and stakeholders
2. **Environment Setup:** Set up development environment with all required tools
3. **Start Phase 1:** Begin with LLM integration and infrastructure setup
4. **Iterative Development:** Follow the phased approach with regular testing
5. **Documentation:** Maintain detailed documentation throughout development
6. **Testing:** Comprehensive testing at each phase
7. **Deployment:** Gradual rollout with monitoring

---

## Notes and Considerations

### Cost Management
- Monitor LLM API usage closely (target: <$100/month for MVP)
- Implement caching aggressively for repeated queries
- Use prompt engineering to minimize token usage
- Consider cheaper models for non-critical tasks

### Performance
- All AI operations async (don't block UI)
- Set realistic timeout limits (30s, 45s, 60s, 10s)
- Implement proper retry logic
- Cache frequently accessed data

### Quality
- Validate all LLM outputs (structure, completeness)
- Implement fallbacks for failures
- Log all AI interactions for quality monitoring
- Gather user feedback for continuous improvement

### Security
- Store API keys securely (environment variables)
- Sanitize user inputs before sending to LLMs
- Implement rate limiting to prevent abuse
- Follow data privacy regulations (GDPR)

### Scalability
- Design for horizontal scaling
- Use async processing for heavy tasks
- Implement proper database indexing
- Plan for vector database scaling (millions of embeddings)

---

**Document Version:** 1.0
**Last Updated:** December 2024
**Status:** Draft - Ready for Review
