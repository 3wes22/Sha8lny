# Chapter 1 — Introduction

> **Chapter purpose.** Chapter 1 frames the entire thesis. It establishes the real-world
> problem, justifies why it matters, states precisely what the project sets out to achieve,
> bounds the work, formalises the research questions, and lists the contributions. By the end
> of this chapter, a reader who knows nothing about the project should understand *what* was
> built, *why*, and *how the thesis is organised*. **Target length: 8–12 pages.**
>
> **Style.** Funnel structure: start broad (the labour market and AI), narrow to the specific
> problem, then to our specific solution. Every empirical claim about the world carries an
> IEEE citation `[n]`. Claims about our own system are stated as fact.

---

## 1.1 Background and Context

**What to write.** Open with the macro context — youth employment and the technology skills
gap, especially in Egypt and the wider MENA region — then narrow to the technological shift
(cloud platforms, the maturation of machine learning, and the recent emergence of large
language models and retrieval-augmented generation) that makes a new class of career tools
feasible. **(≈3 pages.)**

### 1.1.1 The industry and societal context

Egypt has one of the youngest populations in the MENA region, with a large and growing cohort
entering the labour market each year, and the information-technology sector has become a
national priority for economic growth and job creation [1], [2]. Yet a structural **skills
mismatch** persists: the competencies that universities produce often diverge from those
employers demand, and graduates frequently lack a reliable, objective way to discover which
career paths suit them, to measure how far their current skills are from a target role, and to
translate that gap into an actionable learning plan [2], [3]. The cost of this mismatch is
borne twice — by young people who invest years in skills that do not lead to employment, and
by employers who cannot fill vacancies despite a surplus of nominally qualified candidates [3].

> **Sample paragraph (drop-in).**
> "The transition from formal education to professional employment is, for many young
> Egyptians, an unguided search. Career decisions are made with incomplete information about
> in-demand roles, scattered and often globally-oriented learning resources, and no objective
> baseline of one's own competencies. The consequence is a self-reinforcing loop: uncertainty
> about direction delays skill acquisition, which in turn widens the gap between candidate and
> market, deepening the very uncertainty that began the cycle (Figure 1.1)."

### 1.1.2 Technology evolution that enables a new solution

Three converging technology trends make an integrated, intelligent career platform feasible
today in a way it was not a few years ago:

1. **Web platform maturity.** Modern full-stack frameworks (Django REST Framework on the
   server, React on the client) and managed data services (PostgreSQL, Redis) allow a small
   team to ship a secure, multi-module web application with professional engineering rigour
   [4], [5].
2. **The large-language-model revolution.** Transformer-based LLMs [6] have made
   natural-language understanding and generation broadly accessible through hosted APIs,
   enabling dynamic question generation, free-text evaluation, and conversational guidance
   that previously required bespoke NLP pipelines.
3. **Retrieval-augmented generation (RAG).** Because LLMs can hallucinate and have a fixed
   knowledge cut-off, RAG [7] grounds their output in an external, curated corpus, yielding
   answers that are current, citable, and domain-specific — exactly the properties a career
   advisor must have.

> **Sample paragraph (drop-in).**
> "Where earlier career-guidance software relied on static questionnaires and fixed decision
> trees, the maturation of hosted LLMs and retrieval-augmented generation allows a system to
> *reason* over an evolving, locally-curated knowledge base. This thesis exploits that shift:
> rather than encoding career advice as brittle rules, Sha8lny grounds a general-purpose
> language model in a curated corpus of Egyptian and global career knowledge, producing
> guidance that is both adaptive and verifiable."

### 1.1.3 The problem domain

The problem domain is **AI-assisted career development** for early-career technologists. It
spans four sub-domains that existing tools treat in isolation: (a) **career discovery and
competency assessment**, (b) **personalised skill-roadmap planning**, (c) **job discovery and
matching**, and (d) **conversational career advice**. The central thesis of this project is
that these four are most valuable when **integrated around a single competency profile** and
**localised to the Egyptian market**.

**Visual assets for §1.1**

| Asset | Type | Caption | Placement |
|-------|------|---------|-----------|
| Figure 1.1 | Diagram | "The skills-mismatch loop in the Egyptian technology labour market." | After §1.1.1 |
| Figure 1.2 | Timeline | "Evolution of career-guidance technology, from static questionnaires to retrieval-grounded LLM systems." | After §1.1.2 |

---

## 1.2 Problem Statement

**What to write.** State the problem crisply: the existing problems, the limitations of
current approaches, and the precise research gap. Avoid vague language; each limitation should
be specific and, where it is a claim about the world, cited. **(≈2 pages.)**

### 1.2.1 Existing problems

- **P1 — No objective competency baseline.** Job-seekers self-assess inconsistently; there is
  no lightweight, role-aware tool that produces a structured, comparable skill profile [3].
- **P2 — Fragmented, non-personalised learning.** Learning resources are abundant but
  scattered; learners cannot easily convert a measured gap into an ordered, time-boxed plan.
- **P3 — Opaque, globally-oriented job matching.** Mainstream job boards rank by recency or
  keyword match and rarely explain *why* a job fits a candidate, nor do they centre the
  Egyptian market.
- **P4 — Ungrounded AI advice.** General chatbots answer career questions fluently but without
  citations, currency, or scope control, risking confident misinformation [7].

### 1.2.2 Current limitations

Existing solutions fall into three buckets, each limited:

- **Static assessment tools** use fixed item banks and cannot adapt difficulty or coverage to
  the candidate or to a specific target role.
- **Global learning platforms** (e.g., generic MOOCs and roadmap sites) provide content but
  neither measure the learner nor localise to the Egyptian market.
- **General-purpose LLM chatbots** are fluent but ungrounded, lack a competency model, and do
  not connect advice to concrete jobs or learning resources.

### 1.2.3 The research gap

> **Drop-in problem statement.**
> "Despite a rich ecosystem of assessment tools, learning platforms, job boards, and
> conversational agents, **no single system integrates an adaptive, AI-driven competency
> assessment with retrieval-grounded learning roadmaps, explainable job matching, and a
> cited conversational advisor, localised to the Egyptian technology market.** This thesis
> addresses that gap by designing, implementing, and evaluating such a system."

---

## 1.3 Motivation

**What to write.** Explain why the project matters — practically (for users and the local
economy) and scientifically (as a systems-integration and evaluation contribution).
**(≈1–1.5 pages.)**

- **Practical importance.** A unified, Egypt-aware platform can shorten the time from
  uncertainty to employment, reduce wasted learning effort, and give employers better-prepared
  candidates [1]–[3].
- **Scientific importance.** The project demonstrates how to **compose** modern AI building
  blocks (LLMs, RAG, learning-to-rank, adaptive assessment) into a coherent, *deterministic*
  product workflow with **reproducible evaluation** — a recurring challenge as AI moves from
  research demos into engineered systems [7], [8].
- **Personal/academic motivation.** As computer-science students entering this very market, we
  experienced the problem first-hand, which informed both the requirements and the localisation
  choices.

> **Sample paragraph (drop-in).**
> "Beyond its immediate utility, Sha8lny is a case study in *responsible AI engineering*: it
> treats the language model as one untrusted component within a deterministic pipeline,
> grounds its claims in a citable corpus, and subjects its machine-learning components to
> baseline-compared, reproducible evaluation. We argue that this engineering discipline — not
> any single model — is what turns probabilistic AI into a dependable product."

---

## 1.4 Objectives

**What to write.** State one general objective and several specific, measurable objectives.
Use the SMART framing so they can be checked in Chapter 6. **(≈1 page.)**

### 1.4.1 General objective

> To design, implement, and evaluate **Sha8lny**, an integrated, AI-powered career-empowerment
> platform that guides early-career technologists in the Egyptian market from self-assessment
> to employment through adaptive assessment, personalised roadmaps, explainable job matching,
> and grounded conversational advice.

### 1.4.2 Specific and measurable objectives

| # | Objective | Measurable success criterion |
|---|-----------|------------------------------|
| O1 | Build a two-stage adaptive assessment that produces a structured competency profile across 8 roles | Generates valid, role-aware questions for all 8 roles; computes a deterministic weighted score independent of the LLM's self-report |
| O2 | Generate personalised learning roadmaps grounded in a curated corpus | Produces an ordered, phase-structured roadmap from retrieved sources for each target role, with deterministic fallback |
| O3 | Provide explainable, locally-relevant job matching | Returns skill-matched jobs re-ordered by a learning-to-rank model; exposes a human-readable match explanation |
| O4 | Deliver a retrieval-grounded conversational advisor | Answers in-scope questions with cited sources and refuses or redirects out-of-scope queries |
| O5 | Engineer a secure, maintainable, well-tested full-stack system | JWT-secured REST API; **382** automated backend tests passing; documented architecture |
| O6 | Evaluate the AI components reproducibly against baselines | Ranker evaluated by LOO-CV against overlap and random baselines; RAG evaluated on a labelled query set |

---

## 1.5 Scope

**What to write.** Bound the work explicitly: what is included, what is excluded, and the
operating assumptions. A precise scope protects the thesis from "why didn't you do X?"
critiques. **(≈1 page.)**

### 1.5.1 Included features

- Email/password authentication with JWT, profile and skills management, and user preferences.
- Two-stage adaptive, AI-generated competency assessment for 8 technology roles with
  deterministic weighted scoring.
- AI-assembled personalised learning roadmaps with phases, milestones, and matched courses,
  plus a deterministic template fallback.
- Job search, skill-based matching, and LightGBM learning-to-rank ordering, with saved jobs and
  market-insight scaffolding.
- Retrieval-grounded conversational career advisor with citations and scope control.
- Progress tracking, in-app notifications, and resume/portfolio tooling (structured output).

### 1.5.2 Excluded features (and why)

- **Live third-party job ingestion at production scale** — the ranker is trained and evaluated
  on a synthetic Egyptian-tech fixture set; large-scale Wuzzuf/Bayt ingestion is future work.
- **PDF/DOCX export of resumes** — the career-tools endpoints return structured JSON; binary
  export is deferred to a future version.
- **Email/push notification delivery** — models, signals, and preferences exist; outbound
  delivery is stubbed.
- **Native mobile apps** — the client is a responsive web SPA.

### 1.5.3 Assumptions

- Users have basic digital literacy and reliable internet access for the hosted-LLM path.
- The hosted Gemini API is available in the demo environment; otherwise the local Ollama/Gemma
  fallback is used.
- The curated knowledge corpus is representative enough for guidance purposes; it is
  expandable.

> `[ASSUMPTION]` The exclusions above mirror the codebase's documented known-issues
> (synthetic ranker data, stubbed notification delivery, JSON-only resume export). Stating them
> as deliberate scope decisions is both honest and academically defensible.

---

## 1.6 Research Questions

**What to write.** One main research question and a small set of sub-questions that the thesis
answers in Chapter 6. **(≈0.5 page.)**

**Main research question (RQ).**

> *Can an integrated, retrieval-grounded AI platform deliver coherent, explainable, and
> locally-relevant career guidance — spanning assessment, learning, job matching, and advice —
> within a single, deterministic, well-engineered system?*

**Sub-questions.**

- **RQ1.** How can an LLM be used to generate adaptive, role-aware competency questions while
  keeping the resulting score *deterministic and trustworthy* rather than relying on the
  model's self-reported score?
- **RQ2.** How effectively can retrieval-augmented generation ground learning roadmaps and
  conversational advice in a curated, locally-relevant corpus?
- **RQ3.** Does a learning-to-rank model improve job ordering over a transparent
  skill-overlap baseline, and can the improvement be measured reproducibly?
- **RQ4.** What architectural patterns make such a multi-module AI system secure, maintainable,
  and testable?

---

## 1.7 Contributions

**What to write.** Separate academic, technical, and practical contributions. **(≈1 page.)**

**Academic contributions.**

- **C1.** A reference architecture for **deterministic orchestration of probabilistic AI** in a
  product setting: the LLM is treated as one untrusted component, with scoring, validation, and
  fallbacks owned by deterministic code.
- **C2.** A **reproducible evaluation methodology** for a small-data job ranker (leave-one-group
  -out cross-validation against transparent baselines) and a labelled RAG retrieval set.

**Technical contributions.**

- **C3.** A working **hybrid RAG pipeline** (dense + BM25 + reciprocal rank fusion +
  cross-encoder reranking + abstention) over ChromaDB, integrated into both assessment and
  advisory features.
- **C4.** A **two-stage adaptive assessment engine** with role-graph-driven coverage allocation
  and weighted, deterministic scoring across 8 roles.
- **C5.** A **modular-monolith full-stack implementation** (Django REST + React/TypeScript +
  an `ai-models` package) with JWT security, OpenAPI documentation, and 350+ automated tests.

**Practical contributions.**

- **C6.** An **Egypt-localised** career platform that integrates assessment, roadmaps, jobs, and
  advice around a single competency profile — addressing the fragmentation that motivated the
  project.

---

## 1.8 Thesis Organisation

**What to write.** A short paragraph per chapter so the reader can navigate. **(≈0.5 page.)**

- **Chapter 2 — Literature Review.** Surveys career-recommendation systems, LLMs, RAG,
  learning-to-rank, and adaptive assessment; presents a comparison matrix and a formal
  gap analysis.
- **Chapter 3 — Methodology & System Design.** Captures functional and non-functional
  requirements, the system architecture, design decisions and trade-offs, data-flow diagrams,
  and the full UML model set.
- **Chapter 4 — System Implementation.** Details the development environment and the concrete
  implementation of every module, the database/ERD, the API, security, and the user interface.
- **Chapter 5 — Testing & Evaluation.** Presents the testing strategy and the empirical
  evaluation of the AI components, with results tables and analysis.
- **Chapter 6 — Discussion.** Interprets the findings, answers the research questions, validates
  the contributions, compares with the literature, and discusses trade-offs and limitations.
- **Chapter 7 — Conclusion & Future Work.** Summarises achievements and proposes short-term and
  long-term extensions.

---

## Chapter 1 — Visual assets summary

| # | Type | Caption | Placement |
|---|------|---------|-----------|
| Figure 1.1 | Diagram | "The skills-mismatch loop in the Egyptian technology labour market." | §1.1.1 |
| Figure 1.2 | Timeline | "Evolution of career-guidance technology toward retrieval-grounded LLM systems." | §1.1.2 |
| Figure 1.3 | Block diagram | "Sha8lny at a glance: four integrated services around one competency profile." | §1.1.3 or §1.7 |
| Table 1.1 | Table | "Specific, measurable objectives and their success criteria." | §1.4.2 |
| Table 1.2 | Table | "Project scope: included vs. excluded features." | §1.5 |

**Citations introduced in this chapter:** [1]–[8] (see `08-references.md`).
