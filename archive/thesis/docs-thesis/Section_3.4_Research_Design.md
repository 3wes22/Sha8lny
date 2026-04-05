# 3.4 Research Design

## 3.4.1 Research Approach

This project adopts the **Design Science Research (DSR)** methodology, which emphasizes the creation and evaluation of IT artifacts to address practical problems (Hevner et al., 2004). DSR is appropriate for this study because the primary contribution is a functional software platform that addresses an identified gap in AI-powered career guidance for the Egyptian market.

The research follows an iterative cycle: problem identification, artifact design, development, evaluation, and refinement. This enables continuous improvement based on empirical feedback while producing both a practical solution and generalizable design knowledge.

## 3.4.2 Development Strategy

### Phased Implementation

The platform was developed using an **incremental MVP (Minimum Viable Product)** strategy, progressing through seven phases:

1. **Foundation** — Authentication, user profiles, testing infrastructure
2. **Assessment** — Career assessment questionnaire and scoring mechanism
3. **Roadmaps** — Learning pathway templates and progress tracking
4. **Jobs** — Job aggregation and basic matching
5. **Advisory** — Conversational career guidance interface
6. **AI Integration** — Local LLM deployment and model fine-tuning
7. **Analytics** — Progress visualization and dashboard metrics

This phased approach reduces technical risk by validating core workflows before introducing AI complexity, and enables early feedback collection.

### Agile Practices

Development followed agile principles with two-week iterations, continuous integration testing, and version-controlled documentation. Test-driven development (TDD) ensured code reliability, with automated test suites validating each module before integration.

## 3.4.3 AI/ML Methods

The platform incorporates four AI components, each selected based on task requirements and resource constraints:

| Component | Method | Rationale |
|-----------|--------|-----------|
| Skill Assessment | QLoRA fine-tuned LLaMA 3.1 (8B) | Enables domain-specific evaluation with limited compute |
| Learning Roadmap | Prompt-engineered Mistral 7B | Zero-shot generation sufficient for structured output |
| Career Advisory | RAG with Mistral 7B + ChromaDB | Grounds responses in curated knowledge, reduces hallucination |
| Job Matching | Hybrid content-based + LightGBM ranking | Combines semantic similarity with learned preferences |

**QLoRA (Quantized Low-Rank Adaptation)** was selected for fine-tuning because it reduces memory requirements from >40GB to ~5GB VRAM, enabling training on free-tier GPU resources while maintaining model quality.

**Retrieval-Augmented Generation (RAG)** was implemented for the advisory module to provide contextually grounded responses. User queries are embedded and matched against a curated knowledge base; relevant chunks are concatenated with the prompt before generation, improving factual accuracy without requiring fine-tuning.

## 3.4.4 Data Collection

| Data Type | Source | Method |
|-----------|--------|--------|
| Assessment questions | Synthetic generation | LLM-generated with manual validation |
| Career knowledge base | Industry publications | Manual curation |
| Job listings | Egyptian job platforms | API integration |
| User interactions | Platform usage | Application logging |

Due to the absence of existing Egyptian career guidance datasets, training data was synthetically generated using large language models, then filtered and validated by domain review. This approach balances data quality with resource constraints.

## 3.4.5 Evaluation Methods

**Software Quality**: Automated testing with pytest (>80% coverage target for critical paths), TypeScript strict mode for type safety, and continuous integration pipelines.

**AI Components**: Model outputs evaluated through JSON schema validation (roadmaps), retrieval precision metrics (RAG), and structured test cases. Human review was conducted for assessment question validity and response quality.

**User Validation**: Planned usability testing with task completion metrics and System Usability Scale (SUS) questionnaire.

## 3.4.6 Constraints and Mitigations

| Constraint | Mitigation |
|------------|------------|
| Zero budget for cloud APIs | Open-source models (LLaMA, Mistral), local deployment via Ollama |
| Limited compute resources | 4-bit quantization, QLoRA, free GPU tiers |
| No domain-specific dataset | Synthetic data generation with validation |
| Single-developer scope | MVP prioritization, phased delivery |

## 3.4.7 Summary

The research design integrates Design Science Research methodology with agile development practices and parameter-efficient AI techniques. This combination enables the creation of a functional AI-powered career platform within academic resource constraints while maintaining systematic rigor through iterative evaluation and documented design decisions.

---

**Word Count**: ~550 words
