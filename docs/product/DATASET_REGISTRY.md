# Dataset Registry

Decision registry for every data source the platform ingests. Detailed
provenance lives in [`ai-models/data/CITATIONS.md`](../../ai-models/data/CITATIONS.md);
this file adds the **decision layer**: license check, credibility rationale, and
USE/REJECT status. **Rule (binding, from the 2026-06-10 spec): a source gets its
entry here — license checked — *before* any ingestion code runs.**

Quality tiers used by retrieval confidence scoring: `official` (government/
standards bodies), `established` (recognized platforms/publishers),
`curated` (team-authored), `dev_fallback` (license-restricted, never defended).

---

## Ingested sources

### O*NET Database 30.1
- **Source URL:** https://www.onetcenter.org/database.html
- **License:** CC BY 4.0 — attribution required ("This page includes information
  from O*NET … under the CC BY 4.0 license. O*NET is a trademark of USDOL/ETA.")
- **Size:** full text DB (`db_30_1_text/`); 7 whitelisted files currently embedded
- **Quality:** official (USDOL/ETA), peer-maintained occupational taxonomy; US-centric
- **Credibility rationale:** the canonical occupational-information source backing
  decades of labor research; the strongest license + authority combination in the corpus.
- **Decision:** **PARTIAL** — keep `Occupation Data` (titles + rich descriptions)
  and `Task Statements` for RAG; keep the full DB for the roadmap crosswalk
  (`onet_mapper.py`). **Exclude bulk numeric rating rows (Skills/Abilities/Work
  Activities/Knowledge data-value rows) from the RAG collection**: the
  2026-06-10 baseline eval (`ai-models/eval_results/retrieval/baseline.json`)
  shows 358,992 embedded docs dominated by these near-identical rows, drowning
  curated content (recall@5 = 0.067; 44/52 advisory queries return nothing).
  Numeric ratings stay available for structured lookups, not semantic retrieval.

### roadmap.sh content snapshot
- **Source URL:** https://github.com/kamranahmedse/developer-roadmap
- **License:** Proprietary — personal use only; redistribution prohibited
  (see compliance risk in CITATIONS.md)
- **Size:** ~9,872 markdown files under `ai-models/data/roadmap-sh-data/src/data/`
- **Quality:** established platform, community-maintained, globally generic
- **Credibility rationale:** de-facto industry-standard learning paths; high content
  quality but unusable as a defended/redistributed corpus due to license.
- **Decision:** **PARTIAL — `dev_fallback` only.** Tagged `quality_tier: dev_fallback`
  in the collection; never cited as a defended source; replacement by licensable
  equivalents is the Task 1.5 acquisition goal. Pre-publication remediation
  (runtime fetch / consent / replacement) per CITATIONS.md stands.

### Curated knowledge base (`ai-models/data/knowledge_base/*.md`)
- **Source:** team-authored (4 files: career fundamentals, Egyptian market,
  learning paths, skill assessment)
- **License:** project-internal (no external restriction)
- **Size:** 4 markdown files, section-structured
- **Quality:** curated; Egypt-specific — the only Egypt-focused prose in the corpus
- **Credibility rationale:** written for this platform's exact audience; weakness:
  market/salary statements currently carry no external citations.
- **Decision:** **USE**, tier `curated`. Improvement noted for Task 1.5/1.7:
  back salary/market claims with citations to official Egyptian sources where
  acquirable.

### `jobs_egypt_tech.csv` (job-ranker fixtures)
- **Source:** hand-authored synthetic fixtures (~60 rows), real company names,
  templated descriptions
- **License:** internal/synthetic
- **Quality:** synthetic — **not market data**
- **Credibility rationale:** none as evidence; exists to demonstrate the ranking
  pipeline and evaluation methodology end-to-end (per `EVAL_REPORT.md`).
- **Decision:** **PARTIAL — dev/test only.** ⚠️ Registry finding (2026-06-10):
  `CLAIMS_REGISTER.md` C6 marks real-market ingest as Done citing this file, but
  CITATIONS.md correctly records real postings as *not yet acquired*. C6 must be
  re-labeled until plan Tasks 3.1–3.2 land ≥100 genuinely real postings.

### Course catalog (`seed_courses`)
- **Source:** seeded catalog referencing real course platforms
- **License:** metadata only (titles/links), no content redistribution
- **Quality:** established platforms (links out)
- **Decision:** **USE** for course↔milestone matching (metadata-level only).

### Assessment scenario corpus (`Backend/apps/assessments/scenario_corpus/`)
- **Source:** team-authored scenario documents (currently `backend.py` only)
- **License:** project-internal
- **Decision:** **USE**, tier `curated`. New role content (plan Tasks 2.6–2.8)
  must log any external references it draws on as entries here first.

---

## Approved candidate sources (Task 1.5 — license verified 2026-06-10, ingestion in Task 1.7)

### BLS Occupational Outlook Handbook (OOH)
- **Source URL:** https://www.bls.gov/ooh/ (republishing guidance: https://www.bls.gov/ooh/about/ooh-developer-info.htm)
- **License:** U.S. federal government work — public domain (17 U.S.C. §105); BLS
  publishes explicit data-access and republishing guidance
- **Size:** 300+ occupation profiles ("what they do", "how to become one", "pay",
  "job outlook") — semantically rich career prose
- **Quality:** official (USDOL/BLS); US-centric like O*NET, used as occupational
  reference, not Egyptian market data
- **Credibility rationale:** government statistical agency; the strongest possible
  license; prose (unlike O*NET numeric rows) embeds and retrieves well.
- **Decision:** **USE**, tier `official`. Ingest the ~25 computer/IT occupation
  profiles relevant to the platform's 8 roles.

### MDN Web Docs (prose content)
- **Source URL:** https://developer.mozilla.org/ (license page:
  /en-US/docs/MDN/Writing_guidelines/Attrib_copyright_license)
- **License:** CC-BY-SA 2.5 or later for prose; attribution to "Mozilla
  Contributors" + source link required; share-alike on reuse
- **Size:** ingest selectively — concept/guide pages for web fundamentals
  (HTTP, JavaScript, accessibility, web security basics)
- **Quality:** established (Mozilla); industry-reference documentation
- **Credibility rationale:** the de-facto authoritative web-platform documentation,
  openly licensed — a license-clean replacement for part of roadmap.sh's role.
- **Decision:** **USE**, tier `established`, with per-chunk attribution metadata
  (url + "Mozilla Contributors, CC-BY-SA 2.5+").

> **Ingestion status (2026-06-10):** MCIT/ITIDA and the Stack Overflow survey
> are now ingested as authored excerpt-and-cite summaries under
> `ai-models/data/knowledge_base/egypt_official/` and `tech_trends/`
> (per-fact citations inline; provenance headers; validated by
> `src/rag/corpus_validation.py` before embedding). BLS OOH and MDN were
> ingested in plan Task 1.7. Every fetched/authored corpus file must pass the
> validation layer (provenance header, length, structure, junk and control
> character checks); exact-duplicate chunks are dropped per (source, category)
> at build time.

### Stack Overflow Annual Developer Survey (public dataset)
- **Source URL:** https://survey.stackoverflow.co/ (data under ODbL per SO's
  public data releases)
- **License:** Open Database License (ODbL 1.0) — attribution, keep-open on
  redistribution, share-alike for adapted databases
- **Size:** ~65k responses/year; tabular
- **Quality:** established; global (not Egypt-specific); self-selected sample —
  noted as a bias
- **Credibility rationale:** largest recurring developer survey; standard source
  for technology-adoption and career-trend claims.
- **Decision:** **PARTIAL** — do not embed raw rows; derive short attributed
  summary passages (technology popularity, learning trends) for the curated
  knowledge base, citing survey year.

### MCIT / ITIDA official Egypt ICT publications
- **Source URLs:** https://mcit.gov.eg/en/Publications (ICT Indicators monthly +
  quarterly bulletins, MCIT Yearbook), https://itida.gov.eg (Industry Outlook,
  talent-landscape pages, Digital Egypt Strategy for Offshoring 2022–2026)
- **License:** official government publications; no explicit open license —
  reuse as cited facts/excerpts with attribution, no bulk republication of PDFs
- **Size:** selective — sector growth, employment, talent-pool, and
  capacity-building program facts
- **Quality:** official (Egyptian government / IT development authority)
- **Credibility rationale:** the missing piece — *official Egyptian* grounding for
  the Egypt-market claims currently uncited in `egyptian_market.md` (e.g., ICT
  sector growth 14–16%/yr, 2025 digital exports USD 4.8B, DEPI/DEBI training
  initiatives, 240+ offshoring companies).
- **Decision:** **USE (excerpt-and-cite)**, tier `official`. Authored summary
  passages with per-fact citations enter the curated knowledge base; PDFs are
  not vendored into the repo.
