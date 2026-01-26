# Chapter 2: Related Work - Quick Reference Guide

## Target Metrics
- **Total Length**: 8-12 pages (2,400-3,600 words)
- **Citations**: 40-60 references
- **Timeline**: 4 weeks
- **Sections**: 5 main sections

---

## Section Breakdown

| Section | Title | Length | Words | Citations | Key Focus |
|---------|-------|--------|-------|-----------|-----------|
| 2.1 | Introduction to Literature Review | 0.5-1 pg | 150-300 | 8-12 | Frame 4 domains |
| 2.2 | Historical Perspective | 1.5-2 pg | 450-600 | 8-12 | Evolution timeline |
| 2.3 | Theoretical Framework | 2-3 pg | 600-900 | 12-16 | Architecture + AI theory |
| 2.4 | Previous Research & Studies | 3-4 pg | 900-1200 | 15-20 | Gap analysis |
| 2.5 | Current State of the Field | 1.5-2 pg | 450-600 | 8-12 | Recent advances |

---

## Four Domains to Research

### 1. Career Assessment Systems
**Keywords**: AI skill assessment, psychometric testing, adaptive testing, question generation
**Your Tech**: LLaMA 3.1 8B, QLoRA fine-tuning, 5 assessment types
**Code Reference**: `Backend/apps/assessments/models.py`

### 2. Learning Path Personalization
**Keywords**: Adaptive learning, curriculum sequencing, educational recommender systems
**Your Tech**: Mistral 7B, hierarchical roadmaps (Phases → Milestones → Skills)
**Code Reference**: `Backend/apps/roadmaps/models.py`

### 3. Conversational AI & RAG
**Keywords**: Retrieval-augmented generation, chatbots, semantic search, ChromaDB
**Your Tech**: Sentence-Transformers + ChromaDB + Mistral 7B
**Code Reference**: `ai-models/CLAUDE.md:138-151`

### 4. Job Recommendation Systems
**Keywords**: Skill-job matching, hybrid recommenders, learning-to-rank, explainability
**Your Tech**: LightGBM ranker, skill embeddings, Egyptian market
**Code Reference**: `Backend/apps/jobs/models.py`

---

## Commercial Platforms to Compare

| Platform | What They Do | What They Lack | Sha8lny Advantage |
|----------|--------------|----------------|-------------------|
| LinkedIn Learning | Courses + Jobs | No assessment, no personalized roadmaps | AI assessment → adaptive roadmaps |
| Coursera Career Academy | Courses + Basic assessment | No job integration, no advisory | Full integration across 4 domains |
| Pathrise | Mentored career coaching | Not scalable, expensive ($4k-9k) | Scalable AI at $0 cost |
| Wuzzuf | Egyptian job listings | No learning paths, no assessment | Learning integrated with jobs |

---

## Key Papers to Find

### Foundational (Must-Have)
- Brown et al. (2020) - GPT-3 paper
- Lewis et al. (2020) - RAG paper
- Hu et al. (2021) - LoRA paper
- Touvron et al. (2023) - LLaMA 2 paper
- Jiang et al. (2023) - Mistral 7B paper
- Dettmers et al. (2023) - QLoRA paper

### Career Assessment
- Papers on computerized adaptive testing (CAT)
- AI question generation
- Psychometric validation

### Learning Paths
- Educational recommender systems
- Curriculum sequencing
- Knowledge tracing models

### RAG & Chatbots
- Vector database benchmarks
- Conversational AI surveys
- Domain-specific chatbots

### Job Recommendations
- Skill-job matching algorithms
- LinkedIn/Indeed recommendation systems
- Explainable recommender systems

---

## Code References to Include

Use this format when citing your implementation:

```markdown
Sha8lny implements RAG with ChromaDB vector storage
(ai-models/CLAUDE.md:146), Sentence-Transformers embeddings
(ai-models/CLAUDE.md:143), and Mistral 7B for generation.

The assessment module supports five types—skills, career_interests,
personality, learning_style, comprehensive
(Backend/apps/assessments/models.py:30-36).

RoadmapCourse entities link learning milestones to job market demand
through LightGBM ranking (Backend/apps/roadmaps/models.py:667-762).
```

---

## Gap Statement Template

**Use this structure in Section 2.4**:

> "Existing platforms provide partial solutions:
> - **LinkedIn Learning** offers courses and job listings but lacks AI-driven skill assessment and personalized roadmap generation.
> - **Coursera Career Academy** provides basic assessments and courses but does not integrate job market data or conversational advisory.
> - **Pathrise** delivers human-mentored coaching but cannot scale economically, limiting accessibility.
> - **Wuzzuf** focuses solely on Egyptian job listings without addressing skill development.
>
> No existing platform integrates all four components—AI assessment, adaptive learning paths, RAG-based advisory, and job matching—within a unified architecture. Sha8lny addresses this gap through a modular monolithic design (docs/ARCHITECTURE.md:10-43) enabling cross-module workflows (assessment → roadmap → job recommendations) with shared user context, Egyptian market focus, and zero API costs through self-hosted LLMs."

---

## Writing Tips

### Do's ✅
- Start every claim with evidence (citation or code reference)
- Use critical analysis, not just summary
- Link theory to your specific implementation
- Include diagrams (RAG pipeline, architecture)
- Create comparison tables
- Cite both academic papers AND technical documentation

### Don'ts ❌
- Don't just list features of platforms—analyze gaps
- Don't cite Wikipedia or blogs (use academic sources)
- Don't forget Egyptian market context
- Don't make unsupported claims about "first" or "only"
- Don't skip code references—they prove implementation

### Paragraph Template
```
[Topic sentence with theoretical foundation + citation]
[Existing research/platform approach + citation]
[Limitation or gap identified]
[How Sha8lny addresses it with specific implementation + code reference]
[Outcome or advantage]
```

---

## 4-Week Timeline (Quick View)

**Week 1**: Research (30-40 papers, annotate, outline)
**Week 2**: Write first draft Sections 2.1-2.4 (~2,900 words)
**Week 3**: Complete 2.5, revise, add diagrams (~1,500 more words)
**Week 4**: Peer review, incorporate feedback, finalize

**Daily Target**: 300-600 words (1-2 hours)

---

## Quality Checkpoints

### After Week 2
- [ ] Sections 2.1-2.4 drafted (~3,000 words)
- [ ] 25-30 citations added
- [ ] At least 1 comparison table created
- [ ] All four domains covered

### After Week 3
- [ ] All sections complete (3,500+ words)
- [ ] 40+ citations with complete bibliography
- [ ] 2-3 diagrams (RAG, architecture, timeline)
- [ ] All code references verified

### Before Submission
- [ ] 8-12 pages formatted
- [ ] 40-60 citations, consistent style
- [ ] Gap identification clear and compelling
- [ ] Advisor feedback incorporated
- [ ] Proofread for typos/grammar

---

## Search Queries (Copy-Paste Ready)

**Google Scholar**:
```
"AI-powered skill assessment" machine learning
"retrieval augmented generation" career
"learning path recommendation" personalization
"job recommender system" explainability
"LLaMA" fine-tuning LoRA
"parameter-efficient fine-tuning" survey
"vector database" performance comparison
```

**arXiv**:
```
cat:cs.AI "career assessment"
cat:cs.LG "adaptive learning"
cat:cs.CL "retrieval augmented generation"
cat:cs.IR "job recommendation"
```

---

## Egyptian Market Context Sources

- World Bank: Egypt Skills Reports
- ILO: MENA Labor Market Studies
- McKinsey: Egypt Digital Economy Reports
- Egyptian Ministry of Education statistics
- Wuzzuf/Bayt job market trends (cite if available)

Search: "Egypt" + "digital skills gap", "MENA" + "career development", "Egyptian job market" + "technology adoption"

---

## Contact Checklist

- [ ] Schedule weekly advisor meetings
- [ ] Request university library research workshop
- [ ] Identify 2-3 peers for draft review
- [ ] Set up Zotero/Mendeley citation manager
- [ ] Join thesis writing group (if available)

---

## Emergency Contacts

**If stuck on**:
- **Literature search**: University librarian
- **Citation formatting**: Writing center
- **Technical accuracy**: Project team members
- **Structure/content**: Thesis advisor

---

## Final Reminder

**Your Unique Value Proposition**:
> Sha8lny is the first platform to integrate AI-powered assessment, adaptive roadmap generation, RAG-based advisory, and job matching in a unified architecture targeting the Egyptian market—implemented entirely with zero-cost open-source models (LLaMA 3.1, Mistral 7B, ChromaDB) through parameter-efficient fine-tuning (QLoRA) and self-hosting.

**Use this statement to frame your gap analysis throughout Chapter 2.**

---

**Quick Reference Version**: 1.0
**Companion Document**: Chapter_2_Roadmap.md (full guide)
**Last Updated**: January 21, 2026
