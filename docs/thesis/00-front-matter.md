# Front Matter

> **How to use this file.** Each section gives (a) its *purpose*, (b) *expected length*,
> (c) the *writing style*, and (d) *ready-to-use example content* drafted for Sha8lny.
> Replace the bracketed placeholders such as `[University Name]` with your institution's
> details. Front matter is paginated in lower-case Roman numerals (i, ii, iii, …); Arabic
> numerals (1, 2, 3, …) begin at Chapter 1.

---

## 1. Cover Page

**Purpose.** The outermost page (often a hard/soft binding cover). It carries the title,
authors, institution, and year in the most condensed, formal form. No abstract, no page
number.

**Expected length.** 1 page.

**Writing style.** Centered, formal, minimal text, institutional logo at the top.

**Example content.**

```
[University Logo]

[University Name]
[Faculty of Computers and Artificial Intelligence / Faculty of Engineering]
[Department of Computer Science]

SHA8LNY
An AI-Powered Career Empowerment Platform for the Egyptian Job Market

A Graduation Project submitted in partial fulfilment of the requirements
for the degree of Bachelor of Science in Computer Science

By
[Student Name 1] — [ID]
[Student Name 2] — [ID]
[Student Name 3] — [ID]
[Student Name 4] — [ID]

Supervised by
[Dr. Supervisor Name]

[Academic Year, e.g., 2025 – 2026]
```

---

## 2. Title Page

**Purpose.** The first *internal* page. It repeats the cover information but adds full
supervisory detail and the formal degree statement. This is the page examiners cite.

**Expected length.** 1 page (numbered `i`, usually counted but not printed).

**Writing style.** Identical formality to the cover, with complete names and titles.

**Example content.** As the cover, plus:

```
Project Supervisor:   [Dr. Name], [Title], [Department]
Co-Supervisor (if any): [Name]
Submission Date:      [Month, Year]
```

---

## 3. Approval Page (Examination Committee Sign-off)

**Purpose.** A formal record that the thesis was examined and approved. Contains signature
lines for the supervisor and committee members.

**Expected length.** 1 page.

**Writing style.** Formal, third person, declarative.

**Example content.**

> This is to certify that the graduation project entitled **"Sha8lny: An AI-Powered Career
> Empowerment Platform for the Egyptian Job Market"** has been carried out by the
> above-named students under our supervision and is approved in partial fulfilment of the
> requirements for the degree of Bachelor of Science in Computer Science at
> [University Name].
>
> | Role | Name | Signature | Date |
> |------|------|-----------|------|
> | Supervisor | [Dr. Name] | __________ | ______ |
> | Examiner 1 | [Name] | __________ | ______ |
> | Examiner 2 | [Name] | __________ | ______ |
> | Head of Department | [Name] | __________ | ______ |

---

## 4. Declaration (Statement of Originality)

**Purpose.** A signed statement that the work is the authors' own and that all external
material is properly cited. Required to satisfy academic-integrity policies.

**Expected length.** Half a page.

**Writing style.** First person plural, formal, legally toned.

**Example content.**

> We hereby declare that this graduation project, *Sha8lny: An AI-Powered Career Empowerment
> Platform for the Egyptian Job Market*, is the result of our own work and effort, except
> where otherwise acknowledged. All sources of information and external material have been
> duly cited in accordance with IEEE referencing conventions. This work has not been
> submitted, in whole or in part, for any other degree or qualification at this or any other
> institution. We further declare that all third-party datasets and content used during
> development (including the O*NET 30.1 database and the roadmap.sh content snapshot) are
> used in compliance with their respective licences and are clearly attributed in this
> document.
>
> Signed: ____________________  Date: __________

> `[ASSUMPTION]` We state IEEE referencing and the specific third-party datasets because the
> codebase ships an O*NET (CC BY 4.0) crosswalk and a roadmap.sh snapshot under a
> personal-use licence. The declaration foregrounds licence compliance, which strengthens
> the integrity statement.

---

## 5. Acknowledgements

**Purpose.** To thank the supervisor, faculty, families, and any organisations who supported
the project.

**Expected length.** Half to one page.

**Writing style.** First person plural, warm but professional.

**Example content.**

> We extend our deepest gratitude to our supervisor, [Dr. Name], whose guidance, patience,
> and technical insight were instrumental throughout this project. We thank the faculty of
> [Department] for providing the academic foundation that made this work possible, and our
> families for their unwavering support. We also acknowledge the open-source and research
> communities behind Django, React, ChromaDB, sentence-transformers, and LightGBM, whose
> tools underpin our implementation.

---

## 6. Dedication

**Purpose.** A short, personal dedication (optional but customary).

**Expected length.** 1–3 lines, centered on its own page.

**Writing style.** Personal, concise.

**Example content.**

> *To our families, whose belief in us never wavered, and to every young Egyptian searching
> for a clearer path into the technology profession.*

---

## 7. Abstract

**Purpose.** A self-contained summary of the entire thesis: problem, method, system, results,
and conclusion. It is the most-read page; many readers decide from the abstract alone whether
to read further.

**Expected length.** 200–300 words, single paragraph (or two short paragraphs).

**Writing style.** Past tense for what was done, present tense for what the system does.
No citations, no abbreviations that are not expanded, no figures.

**Example content (≈260 words).**

> The Egyptian technology labour market suffers from a persistent skills mismatch: graduates
> struggle to identify in-demand career paths, to objectively measure their competencies, and
> to connect their learning to real job opportunities, while global career tools rarely
> account for local market conditions. This thesis presents **Sha8lny**, a full-stack,
> AI-powered career-empowerment platform that addresses this gap through four integrated
> services. First, a **two-stage adaptive assessment** uses a large language model (LLM),
> grounded by a role-aware retrieval corpus, to generate competency questions and produces a
> deterministic, weighted skill profile. Second, a **personalised learning roadmap** is
> assembled from a retrieval-augmented knowledge base and tailored to the learner's measured
> gaps. Third, a **job-matching service** combines transparent skill-overlap scoring with a
> **LightGBM learning-to-rank** model to order opportunities in the Egyptian market. Fourth, a
> **retrieval-grounded AI advisor** answers career questions with cited sources and an
> in/out-of-scope guard. The platform is engineered as a modular-monolith Django REST backend,
> a React and TypeScript single-page application, and a dedicated machine-learning package
> exposing a hybrid (dense + sparse) retrieval pipeline over a ChromaDB vector store. The
> system was validated through 456 automated tests across the backend and frontend (382 + 74), a
> leave-one-group-out evaluation of the ranker (NDCG@5 = 0.59, exceeding skill-overlap and
> random baselines), and a 55-query retrieval evaluation set. The results demonstrate that
> retrieval-grounded, locally-aware AI services can deliver coherent, explainable career
> guidance, and they establish a reproducible evaluation methodology for future, real-data
> extensions.
>
> **Keywords:** career guidance, large language models, retrieval-augmented generation,
> learning-to-rank, adaptive assessment, Egyptian job market, full-stack web platform.

---

## 8. Arabic Abstract (الملخص)

**Status:** *Not requested for this submission (English-only abstract approved).*

> If your department later requires it, the Arabic abstract should be a faithful translation
> of the English abstract, typeset right-to-left, placed immediately after the English
> abstract, and followed by Arabic keywords (الكلمات المفتاحية). Keep technical terms such as
> "Large Language Model" with a parenthetical English gloss on first mention.

---

## 9. Table of Contents

**Purpose.** A navigable map of every numbered heading with page numbers. Auto-generate it in
your word processor (Word: References → Table of Contents; LaTeX: `\tableofcontents`).

**Expected length.** 2–4 pages.

**Writing style.** Hierarchical, consistent numbering (1, 1.1, 1.1.1).

**Example skeleton.**

```
Abstract ................................................. i
Acknowledgements ........................................ iii
List of Figures ......................................... vii
List of Tables .......................................... ix
List of Abbreviations ................................... xi

1  Introduction .......................................... 1
   1.1  Background and Context ........................... 1
   1.2  Problem Statement ................................ 4
   1.3  Motivation ....................................... 6
   1.4  Objectives ....................................... 7
   1.5  Scope ............................................ 8
   1.6  Research Questions ............................... 9
   1.7  Contributions ................................... 10
   1.8  Thesis Organisation ............................. 11

2  Literature Review .................................... 12
   2.1  Search Strategy ................................. 12
   2.2  Career Recommendation Systems ................... 14
   2.3  LLMs and RAG .................................... 16
   2.4  Learning-to-Rank ................................ 19
   2.5  Adaptive Assessment ............................. 20
   2.6  Comparative Analysis ............................ 21
   2.7  Research Gap .................................... 24

3  Methodology and System Design ....................... 26
   3.1  Requirements Analysis ........................... 26
   3.2  System Architecture ............................. 31
   3.3  Design Decisions and Trade-offs ................. 36
   3.4  Data Flow Diagrams .............................. 39
   3.5  UML Models ...................................... 42

4  System Implementation ............................... 48
5  Testing and Evaluation .............................. 70
6  Discussion .......................................... 84
7  Conclusion and Future Work .......................... 92
References .............................................. 98
Appendices ............................................. 103
```

---

## 10. List of Figures

**Purpose.** Lists every figure number, caption, and page. Auto-generated from figure
captions.

**Expected length.** 1–2 pages.

**Example entries (master list lives in `VISUAL-ASSETS.md`).**

```
Figure 1.1  The skills-mismatch loop in the Egyptian tech market ........ 5
Figure 3.1  High-level system architecture of Sha8lny .................. 32
Figure 3.2  Component architecture (backend modules and AI package) .... 34
Figure 3.3  DFD Level 0 (context diagram) .............................. 39
Figure 3.7  Use-case diagram (all actors) .............................. 43
Figure 4.1  Entity-Relationship Diagram ................................ 55
Figure 4.5  Two-stage assessment pipeline .............................. 61
Figure 5.2  Ranker NDCG@5 vs. baselines ................................ 78
```

---

## 11. List of Tables

**Purpose.** Lists every table number, caption, and page.

**Expected length.** 1 page.

**Example entries.**

```
Table 2.1  Comparison matrix of related career-guidance systems ........ 22
Table 2.2  Research-gap analysis ....................................... 24
Table 3.1  Functional requirements ..................................... 27
Table 3.2  Non-functional requirements ................................. 29
Table 4.1  Database tables and relationships ........................... 56
Table 5.1  Job-ranker evaluation results ............................... 77
```

---

## 12. List of Abbreviations

**Purpose.** Expands every acronym used in the thesis, alphabetically.

**Expected length.** 1–2 pages.

**Example content.**

| Abbreviation | Expansion |
|--------------|-----------|
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| ATS | Applicant Tracking System |
| BM25 | Best Matching 25 (ranking function) |
| CFG | Context-Free Grammar |
| CORS | Cross-Origin Resource Sharing |
| CRUD | Create, Read, Update, Delete |
| CV | Cross-Validation |
| DFD | Data Flow Diagram |
| DRF | Django REST Framework |
| ERD | Entity-Relationship Diagram |
| HS256 | HMAC-SHA-256 (JWT signing algorithm) |
| JWT | JSON Web Token |
| KB | Knowledge Base |
| LLM | Large Language Model |
| LOO-CV | Leave-One-Group-Out Cross-Validation |
| LTR | Learning-to-Rank |
| MAP | Mean Average Precision |
| MENA | Middle East and North Africa |
| MRR | Mean Reciprocal Rank |
| MVP | Minimum Viable Product |
| NDCG | Normalised Discounted Cumulative Gain |
| O*NET | Occupational Information Network |
| ORM | Object-Relational Mapping |
| RAG | Retrieval-Augmented Generation |
| REST | Representational State Transfer |
| RRF | Reciprocal Rank Fusion |
| SPA | Single-Page Application |
| TTL | Time To Live |
| UAT | User Acceptance Testing |
| UML | Unified Modeling Language |
| UUID | Universally Unique Identifier |

---

### Front-matter visual assets

| Asset | Type | Caption | Placement |
|-------|------|---------|-----------|
| University + project logo | Image | — | Cover, title page |
| Signature table | Table | — | Approval page |
