# Chapter 2 — Literature Review

> **Chapter purpose.** Chapter 2 demonstrates command of the field, positions Sha8lny against
> prior work, and justifies the research gap that Chapter 1 announced. It is not a list of
> summaries — it is an *argument* that culminates in a gap. **Target length: 12–18 pages.**
>
> **Style.** Thematic, not chronological. Every system or technique is described, then
> *critiqued* (advantages/disadvantages/use-cases), then compared in a matrix. Each external
> claim carries an IEEE citation.

---

## 2.1 Literature Search Strategy

**What to write.** Make the review *reproducible* by documenting databases, keywords, and
inclusion/exclusion criteria. This shows methodological maturity. **(≈2 pages.)**

### 2.1.1 Databases and sources

The review drew on the following sources:

- **IEEE Xplore** and **ACM Digital Library** — peer-reviewed systems and ML papers.
- **arXiv (cs.CL, cs.IR, cs.LG)** — recent LLM/RAG/IR preprints.
- **Google Scholar** — citation-chaining (forward/backward snowballing) and grey literature.
- **Official technical documentation** — Django, React, ChromaDB, sentence-transformers,
  LightGBM, and Google Gemini, used to ground the engineering claims.
- **Labour-market reports** — national and international youth-employment and skills reports for
  Egypt/MENA.

### 2.1.2 Keywords and query strings

Representative Boolean queries:

- `("career recommendation" OR "career guidance") AND ("machine learning" OR "deep learning")`
- `("large language model" OR LLM) AND ("retrieval augmented generation" OR RAG)`
- `("learning to rank" OR "learning-to-rank") AND ("job recommendation" OR "talent matching")`
- `("adaptive assessment" OR "computerized adaptive testing") AND ("skills" OR "competency")`
- `("skills gap" OR "skills mismatch") AND (Egypt OR MENA OR "Middle East")`

### 2.1.3 Inclusion criteria

- Published 2015–2025 (with seminal exceptions, e.g., the Transformer [6] and BM25 [9]).
- Peer-reviewed, or a widely-cited preprint, or authoritative technical documentation.
- Directly relevant to one of our five themes (career recommendation, LLMs, RAG,
  learning-to-rank, adaptive assessment) or to the Egyptian labour-market context.

### 2.1.4 Exclusion criteria

- Non-English sources without an English abstract.
- Purely commercial white papers lacking methodological detail.
- Works on unrelated recommendation domains (e.g., movies, e-commerce) unless they introduced a
  technique we directly reuse (e.g., NDCG [10]).

**Visual asset for §2.1**

| Asset | Type | Caption | Placement |
|-------|------|---------|-----------|
| Figure 2.1 | PRISMA-style flow | "Literature selection flow: records identified, screened, and included." | After §2.1.4 |

---

## 2.2 Theoretical Background

**What to write.** Define every concept the thesis depends on. For each: *definition,
architecture, advantages, disadvantages, use cases.* This section is the conceptual toolbox
the later chapters assume. **(≈5 pages.)**

### 2.2.1 Large Language Models (LLMs)

- **Definition.** Neural networks, typically based on the Transformer architecture [6], trained
  on large text corpora to model and generate natural language.
- **Architecture.** Stacked self-attention and feed-forward layers; decoder-only variants
  (e.g., the GPT and Gemini families) generate text autoregressively.
- **Advantages.** Strong zero-/few-shot generalisation; flexible natural-language I/O;
  structured-output capability (JSON) usable for downstream pipelines.
- **Disadvantages.** Hallucination; fixed knowledge cut-off; cost/latency of hosted APIs;
  non-determinism that complicates evaluation.
- **Use cases in Sha8lny.** Assessment question generation, free-text answer evaluation,
  roadmap-copy personalisation, and conversational advice.

### 2.2.2 Retrieval-Augmented Generation (RAG)

- **Definition.** A pattern that retrieves relevant documents from an external store and
  conditions the LLM's generation on them [7], improving factuality and currency.
- **Architecture.** *Indexing* (chunk → embed → store) and *querying* (embed query → retrieve
  top-k → optionally rerank → prompt the LLM with retrieved context).
- **Advantages.** Grounded, citable answers; updatable without retraining; domain/locale
  specialisation; supports abstention when evidence is weak.
- **Disadvantages.** Retrieval quality bounds answer quality; chunking and embedding choices
  matter; added latency.
- **Use cases in Sha8lny.** Advisory chat grounding, roadmap structure retrieval, and few-shot
  scenario grounding for assessment generation.

### 2.2.3 Vector Embeddings and Vector Databases

- **Definition.** Dense vector representations of text [11] stored in a similarity-search
  database (here, ChromaDB).
- **Architecture.** A sentence encoder (`all-MiniLM-L6-v2`, 384-d) maps text to vectors; the
  database performs approximate/exact nearest-neighbour search by cosine similarity.
- **Advantages.** Captures semantic similarity beyond keyword overlap; fast retrieval.
- **Disadvantages.** Misses exact-term matches (mitigated by hybrid search); embedding model
  quality is a ceiling.
- **Use cases.** All retrieval features and the job-ranker's `skill_embedding_cosine` feature.

### 2.2.4 Hybrid Retrieval (Dense + Sparse) and Reranking

- **Definition.** Combining dense embedding search with sparse lexical search (BM25 [9]) and
  fusing the rankings (Reciprocal Rank Fusion [12]), then reordering with a cross-encoder
  reranker.
- **Advantages.** Robust to both semantic and exact-term queries; reranking sharpens top-k
  precision; an abstention floor suppresses weak evidence.
- **Disadvantages.** More moving parts; reranking adds latency.
- **Use cases.** The advisory retriever (`retriever.py`).

### 2.2.5 Learning-to-Rank (LTR)

- **Definition.** Supervised ML that orders a list of items by relevance [13]. Approaches are
  *pointwise*, *pairwise*, and *listwise*; LambdaMART/`lambdarank` is a listwise,
  gradient-boosted method.
- **Architecture.** Gradient-boosted decision trees (LightGBM [14]) optimised for a ranking
  metric (NDCG [10]) over query groups.
- **Advantages.** Learns non-linear feature interactions; strong on tabular features; fast.
- **Disadvantages.** Needs graded relevance labels; sensitive to label quality (hence our
  weak-supervision caveat).
- **Use cases.** Re-ordering skill-matched jobs (`JobRanker`).

### 2.2.6 Adaptive / Two-Stage Assessment

- **Definition.** Assessment whose item selection adapts to the candidate or target role,
  conceptually related to computerised adaptive testing [15].
- **Architecture (Sha8lny).** Stage 1 establishes a baseline across role competencies; a gap
  analysis then drives Stage 2 toward weaker areas; scoring is a deterministic weighted
  roll-up.
- **Advantages.** Efficient coverage; targeted measurement; role-awareness.
- **Disadvantages.** Item-generation quality depends on the LLM and grounding corpus; not a
  psychometrically calibrated instrument.
- **Use cases.** The core assessment module.

### 2.2.7 Web and Systems Foundations

- **REST APIs** [16], **JSON Web Tokens** for stateless auth [17], the **modular-monolith**
  pattern as a pragmatic middle ground between monolith and microservices [18], and the
  **single-page-application** model [5]. Each is defined briefly with its trade-offs and tied to
  a Sha8lny design choice (elaborated in Chapter 3).

**Visual asset for §2.2**

| Asset | Type | Caption | Placement |
|-------|------|---------|-----------|
| Figure 2.2 | Diagram | "A canonical retrieval-augmented generation pipeline (indexing and querying paths)." | §2.2.2 |
| Figure 2.3 | Taxonomy tree | "Taxonomy of AI techniques employed in Sha8lny." | End of §2.2 |

---

## 2.3 Related Work Analysis

**What to write.** Survey concrete systems and studies in each theme, then critique them. For
*every* significant work, populate the comparison matrix (§2.4) with: author, year, method,
dataset, technology, results, limitations. **(≈4 pages of prose + the matrix.)**

### 2.3.1 Career and job recommendation systems

Job-recommendation research spans content-based filtering, collaborative filtering, and hybrid
and deep-learning rankers; large-scale industrial systems (e.g., professional-network talent
matching) report strong engagement gains but depend on proprietary interaction data and rarely
expose explanations or localise to specific national markets [13], [19]. Skill-based matching
approaches improve interpretability by reasoning over explicit skill overlap [20], which
motivates our transparent overlap score being retained alongside the learned ranker.

> **Sample critique paragraph (drop-in).**
> "Industrial talent-matching systems achieve high accuracy by mining massive interaction
> logs, but this approach is doubly inaccessible to a graduation project: the data is
> proprietary, and the resulting models are opaque to the very job-seekers they serve. Sha8lny
> instead privileges *explainability and locality*, retaining a transparent skill-overlap score
> as the user-facing match metric while using a learned ranker only to reorder candidates."

### 2.3.2 LLMs and RAG for domain question answering

RAG [7] has become the dominant pattern for grounding LLMs in domain corpora; subsequent work
established hybrid retrieval and reranking as best practice for precision [9], [12], and studies
of hallucination motivate abstention and citation [8]. Few systems in the career domain,
however, combine RAG with scope control and source-credibility tiers, as Sha8lny does.

### 2.3.3 Learning-to-rank for recommendation

LambdaMART-style gradient-boosted rankers [13], [14] are a standard, strong baseline for
list ordering, evaluated with NDCG/MAP [10]. Most reported results assume abundant graded
labels; the *small-data, weak-supervision* regime that a bootstrapping product faces is
under-discussed, which is precisely the regime our evaluation methodology targets.

### 2.3.4 Adaptive assessment and competency modelling

Computerised adaptive testing [15] and competency frameworks (e.g., O*NET [21]) inform our
role-graph and staged design, though our instrument is formative rather than psychometrically
calibrated — a limitation we state explicitly.

### 2.3.5 The Egyptian / MENA labour-market context

National and international reports document the youth skills mismatch in Egypt and MENA
[1]–[3], motivating localisation. No surveyed academic system targets Egyptian technology
careers with an integrated AI platform.

---

## 2.4 Comparative Analysis (Comparison Matrix)

**What to write.** A single matrix that lets the examiner see, at a glance, how each related
work compares — and where the gap is. **(≈1 page; landscape table.)**

**Table 2.1 — Comparison matrix of related work and systems.**

| Ref | Author / System (year) | Method | Dataset | Core technology | Reported result | Key limitation |
|-----|------------------------|--------|---------|-----------------|-----------------|----------------|
| [7] | Lewis et al. (2020) | Retrieval-augmented generation | Open-domain QA (NaturalQ, etc.) | Dense retriever + seq2seq | SOTA on open-domain QA at publication | No domain/locale specialisation; no scope control |
| [9] | Robertson & Zaragoza (2009) | BM25 sparse ranking | TREC collections | Probabilistic lexical model | Strong lexical baseline | Misses semantics; needs hybridisation |
| [12] | Cormack et al. (2009) | Reciprocal Rank Fusion | TREC | Rank fusion | Beats individual rankers | Simple; no learning |
| [13] | Burges (2010) | LambdaMART LTR | Web search (proprietary) | GBDT listwise | Strong NDCG gains | Needs many graded labels |
| [14] | Ke et al. (2017) | LightGBM | Tabular benchmarks | Histogram GBDT | Faster, accurate vs. peers | Tabular features only |
| [19] | Industrial talent matching | Hybrid/deep rankers | Proprietary logs | Deep LTR | High engagement lift | Opaque; proprietary; not localised |
| [20] | Skill-based matching | Content/skill overlap | Public job corpora | Skill graphs | Interpretable matches | Lower ceiling than learned rankers |
| [15] | CAT literature | Item-response adaptive testing | Standardised tests | IRT | Efficient, calibrated | Heavy calibration; not LLM-driven |
| [21] | O*NET (occupational DB) | Occupational taxonomy | US occupations | Curated database | Rich competency model | US-centric; static |
| — | **Sha8lny (this work, 2026)** | **Integrated: staged LLM assessment + RAG roadmaps + LTR jobs + grounded advisor** | **Curated KB + 8-role graph + synthetic Egypt jobs + 55-query eval set** | **Django/React + Gemini + ChromaDB + LightGBM** | **456 app-stack tests pass; NDCG@5 = 0.59 > baselines; cited RAG** | **Synthetic ranker data; formative (non-calibrated) assessment** |

---

## 2.5 Research-Gap Analysis

**What to write.** Convert the matrix into an explicit gap statement: what prior work solved,
what remains unsolved, and how Sha8lny addresses it. **(≈1.5 pages.)**

**Table 2.2 — Research-gap analysis.**

| Dimension | What prior work solved | What remained unsolved | How Sha8lny addresses it |
|-----------|------------------------|------------------------|--------------------------|
| Grounded AI advice | RAG for open-domain QA [7] | Domain + locale specialisation; scope control; source credibility | Career-specific RAG with scope gate, credibility tiers, and citations |
| Job matching | Strong industrial/learned rankers [13], [19] | Explainability + locality + small-data evaluation | Transparent overlap score + LTR reorder; LOO-CV vs. baselines on Egypt-localised data |
| Assessment | Calibrated CAT [15]; competency DBs [21] | Dynamic, role-aware, LLM-generated items with *trustworthy* scoring | Two-stage LLM assessment with deterministic weighted scoring |
| Integration | Point solutions per task | A single profile linking assessment → roadmap → jobs → advice | One competency profile shared across all four services |
| Localisation | Global tools | Egypt-specific technology-career guidance | Egypt-focused corpus, job fixtures, and advisor persona |

> **Drop-in gap statement.**
> "The literature provides strong *components* — RAG for grounding, LambdaMART for ranking,
> CAT for adaptive measurement — but no surveyed system *integrates* them around a single
> competency profile, grounds them in a *locally-curated* corpus, and subjects the result to
> *reproducible, baseline-compared evaluation* for the Egyptian technology market. Sha8lny
> occupies exactly this gap."

**Visual asset for §2.5**

| Asset | Type | Caption | Placement |
|-------|------|---------|-----------|
| Figure 2.4 | Venn / positioning diagram | "Positioning of Sha8lny relative to prior work along grounding, ranking, assessment, and localisation axes." | After Table 2.2 |

---

## 2.6 Summary

Close the chapter with one paragraph restating the gap and forward-referencing Chapter 3:
"Having established the gap, Chapter 3 derives the requirements and architecture that fill it."

---

## Chapter 2 — Visual assets summary

| # | Type | Caption | Placement |
|---|------|---------|-----------|
| Figure 2.1 | PRISMA flow | "Literature selection flow." | §2.1 |
| Figure 2.2 | Pipeline diagram | "A canonical RAG pipeline." | §2.2.2 |
| Figure 2.3 | Taxonomy tree | "Taxonomy of AI techniques employed in Sha8lny." | §2.2 |
| Figure 2.4 | Positioning diagram | "Positioning of Sha8lny relative to prior work." | §2.5 |
| Table 2.1 | Matrix | "Comparison matrix of related work and systems." | §2.4 |
| Table 2.2 | Table | "Research-gap analysis." | §2.5 |

**Citations introduced in this chapter:** [1]–[3], [5]–[21] (see `08-references.md`).
