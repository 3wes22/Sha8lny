# Sha8lny — Project Status & Achievements (For Review)

**Prepared:** 2026-06-13
**Project:** Sha8lny — an AI-powered career empowerment platform for the Egyptian job market
**Scope of this document:** Current state of the system and, in particular, the
knowledge-retrieval (RAG) work completed in this development cycle — the part of
the project most relevant to the questions "how do you know this is correct?" and
"what makes this more than an API wrapper?"

---

## 1. What the system is

Sha8lny guides a user from **assessment → learning roadmap → progress tracking →
job matching → AI career advisor**, end to end. It is a full-stack application:

- **Backend:** Django REST API (modular monolith), JWT auth, PostgreSQL/SQLite.
- **Frontend:** React + TypeScript + Vite.
- **AI layer (`ai-models/`):** a Retrieval-Augmented Generation (RAG) pipeline
  over a curated career-knowledge base, plus a LightGBM job ranker.
- **LLM runtime:** Google Gemini for generation, with deterministic offline
  fallbacks on every AI path so the system degrades gracefully (and demos)
  without network or API quota.

The platform's core flow works end to end and is covered by an automated test
suite: **291 backend tests** and **105 AI-layer tests** passing.

---

## 2. The problem we set out to fix this cycle

The AI **career advisor** was the weakest module. Its answers were often
ungrounded — it would respond confidently without supporting evidence. We
treated this as a *measurement* problem first, not a prompt-tuning problem, and
discovered the real cause was in the **retrieval layer** underneath it.

We built an evaluation harness and measured the existing system **before
changing anything** (the scientific control). The baseline was stark:

- The knowledge collection held **358,992 documents**, ~85% of them
  near-identical numeric data rows from the O\*NET database, pulled in by a
  bug. These drowned out the actual career-guidance content.
- On a 55-question evaluation set, **44 of 55 realistic user questions returned
  zero documents** — the advisor was answering from nothing.
- Recall@5 = **0.118**, Mean Reciprocal Rank = **0.109**.

This is the honest starting point against which all improvement below is measured.

---

## 3. What we built — a defensible retrieval pipeline

We rebuilt the knowledge layer as a measured, staged pipeline. Each technique is
standard in the information-retrieval literature, and each was added **one at a
time with a re-measurement**, so we can attribute the improvement to each step
rather than claiming a single black-box gain.

### 3.1 A license-clean, credible knowledge corpus

Every data source carries a documented license decision **made before
ingestion** (recorded in `docs/product/DATASET_REGISTRY.md`):

| Source | What it provides | License basis | Credibility tier |
|---|---|---|---|
| **O\*NET 30.1** (US Dept. of Labor) | Occupation tasks & titles | CC BY 4.0 | Official |
| **BLS Occupational Outlook Handbook** | What jobs involve, outlook | US public domain | Official |
| **MDN Web Docs** | Web/technical concepts | CC-BY-SA, attributed | Established |
| **ITIDA / MCIT (Egypt government)** | Egyptian ICT market, salaries, gov. training programs | Official publications, excerpt-and-cite | Official |
| **Stack Overflow Developer Survey 2025** | Technology adoption trends | ODbL, attributed summary | Established |
| Curated knowledge base | Egypt-specific career prose | Internal | Curated |
| roadmap.sh | Learning-path structure | Personal-use only | **Dev-fallback only — never cited as a source** |

The Egyptian government sources (ITIDA/MCIT) were acquired specifically to
ground Egypt-market claims — salary ranges, sector growth, and *real, free
government training programs* a student can actually enrol in (DEPI, DEBI, Train
to Hire, ITIDA Gigs). Every fact in those documents carries an inline citation
to its source page.

### 3.2 A validation layer (data quality gate)

No file enters the corpus without passing an automated validation layer
(`src/rag/corpus_validation.py`): it enforces a provenance header
(source, URL, license, capture date), minimum substantive length, heading
structure, and rejects raw-HTML junk and control characters. Exact-duplicate
passages are removed at build time. **This layer proved its worth by catching
its own first regression** — it rejected all 12 MDN files over a header-format
mismatch, which we caught and fixed before the bad build shipped.

### 3.3 Retrieval techniques (each with an academic basis)

1. **Structure-aware chunking** — splits documents on headings into coherent
   passages, replacing a naive fixed-character split that cut sentences in half.
2. **Hybrid search** — combines dense vector (semantic) search with BM25
   (keyword) search, merged via **Reciprocal Rank Fusion** (Cormack et al.,
   SIGIR 2009). This catches both paraphrased questions *and* exact terms like
   occupation codes.
3. **Cross-encoder re-ranking** — a second model re-reads the top candidates
   jointly with the question for a more accurate final ordering (Nogueira & Cho,
   2019).
4. **Citation + confidence tiering** — every retrieved passage is returned with
   its source, URL, and a HIGH / MEDIUM / LOW confidence label.
5. **Source-diversity selection** — caps how many passages come from one
   document section, so answers draw on varied evidence.
6. **Abstention floor** — if the best evidence is too weak (off-topic question),
   the system returns **nothing** and the advisor honestly says it cannot
   answer, rather than fabricating.

---

## 4. The evidence — measured, staged improvement

All numbers below are produced by a reproducible script
(`scripts/run_retrieval_eval.py`) over a 55-question ground-truth set, and every
result file is committed to the repository. **Each row adds one technique to the
row above it.**

| Stage | Recall@5 | Recall@10 | Precision@5 | MRR | Questions with no answer |
|---|---|---|---|---|---|
| Baseline (original system) | 0.118 | 0.118 | 0.055 | 0.109 | 44 / 55 |
| + Clean corpus & chunking | 0.209 | 0.209 | 0.062 | 0.161 | 43 / 55 |
| + Hybrid search (BM25+dense) | 0.536 | 0.673 | 0.175 | 0.396 | 17 / 55 |
| + Cross-encoder re-ranking | 0.627 | 0.682 | 0.226 | 0.553 | 16 / 55 |
| + Egypt sources, validation, diversity | 0.609 | 0.664 | 0.218 | 0.544 | 17 / 55 |
| + Abstention floor | 0.609 | 0.664 | 0.218 | 0.544 | 17 / 55 |

**Headline result: Recall@5 improved ~5× (0.118 → 0.609) and Mean Reciprocal
Rank ~5× (0.109 → 0.544) over the measured baseline.** The collection shrank
from 358,992 to ~64,000 high-quality documents.

The final two rows show deliberate, honest trade-offs: source-diversity costs a
fraction of recall in exchange for less redundant answers, and the abstention
floor is measured at **zero cost** to legitimate questions (identical metrics)
while preventing fabrication on off-topic ones.

---

## 5. Adversarial stress test

Beyond the metric set, we ran 18 adversarial queries (`scripts/stress_test_retrieval.py`)
to probe real robustness. Findings, stated honestly:

| Category | Result |
|---|---|
| Egyptian government programs (new data) | **Excellent** — HIGH-confidence, cited to itida.gov.eg |
| Exact-term / occupation-code lookups | **Excellent** — precise hits |
| Off-topic ("headache medication", "visa") | **Correctly refuses** — returns no answer |
| Paraphrased questions | Good (2 of 3 variants) |
| Misspelled queries | Weak — now safely abstains rather than misleads |
| **Arabic / code-switched queries** | **Fails — known limitation (see §6)** |

Diversity invariants held with zero violations. Retrieval latency is ~0.7s
median after a one-time index warm-up.

### Live demonstration (real Gemini calls)

- *"Are there free government training programs in Egypt for a tech job?"* →
  grounded answer naming DEPI, ITIDA Gigs, and Train to Hire, **cited at HIGH
  confidence with clickable itida.gov.eg links.** (Before this work, this
  question had nothing to retrieve.)
- *"How should I negotiate my first developer salary in Cairo?"* → concrete EGP
  salary ranges drawn from the curated knowledge base plus an official ITIDA
  source.
- *"What medication should I take for a headache?"* → correctly deflected
  without consuming any API call.

---

## 6. Honest limitations (and the path forward)

We document these explicitly rather than hide them — this is core to the
project's credibility.

1. **Arabic and code-switched queries are not yet supported.** The corpus is
   English and the embedding model is English-centric. For an Egyptian platform
   this is the most important gap; the fix is a multilingual embedding model
   plus Arabic content, and it is the top item of future work.
2. **Misspellings degrade retrieval** (the system now safely abstains rather
   than returning wrong results); spelling normalization is future work.
3. **The abstention threshold is tunable** and currently set conservatively;
   one broad conversational query retrieved less context than ideal. Calibrating
   it is a scheduled evaluation task.
4. **The evaluation set is single-annotator** (55 questions) — directionally
   strong but not a multi-rater gold standard.
5. **The job ranker** is trained on synthetic fixtures; replacing it with real
   labeled Egyptian job data is planned but not yet done.

---

## 7. What this demonstrates academically

- **It is not an API wrapper.** There is a real, measured retrieval pipeline —
  hybrid search, fusion, re-ranking, validation, and abstention — between the
  user and the LLM, each component justified by published methods.
- **Correctness is measured, not asserted.** A reproducible evaluation harness
  with a committed ground-truth set produces the numbers in §4; anyone can
  re-run them.
- **The data is credible and traceable.** Every source has a documented license
  and the system cites official Egyptian government and US labor sources by URL.
- **The system knows what it does not know.** The abstention mechanism is rare
  in student RAG projects and directly addresses the "how do you prevent
  hallucination?" question.

---

## 8. Reproducing the results

```bash
# Retrieval evaluation (produces the table in §4)
cd ai-models
../Backend/venv/bin/python scripts/run_retrieval_eval.py --stage <stage-name>

# Adversarial stress test (transcripts in §5)
../Backend/venv/bin/python scripts/stress_test_retrieval.py

# Data-quality validation report
python3 scripts/validate_corpus.py

# Test suites
cd ../Backend && env -u GEMINI_API_KEY ./venv/bin/python -m pytest -q   # 291 passing
cd ../ai-models && ../Backend/venv/bin/python -m pytest -q              # 105 passing
```

**Supporting documents:**
`docs/product/RAG_RETRIEVAL_EVAL.md` (full eval table + stress findings),
`docs/product/DATASET_REGISTRY.md` (every source's license & decision),
`docs/product/CLAIMS_REGISTER.md` (claim-by-claim status).
