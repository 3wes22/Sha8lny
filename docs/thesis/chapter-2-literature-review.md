# Chapter 2 — Literature Review and Related Work

## 2.1 Introduction

This chapter surveys the body of research and the existing systems that inform
the design of Sha8lny. The platform sits at the intersection of several
established fields: career guidance and recommendation systems, personalized and
adaptive learning, machine-learning-based ranking, and the application of
artificial intelligence — in particular large language models (LLMs) and
retrieval-augmented generation (RAG) — to education and advisory tasks. The
purpose of the chapter is twofold. First, it establishes the academic and
practical context in which the project is situated, demonstrating an
understanding of the techniques that the system actually employs. Second, it
analyzes the strengths and limitations of existing platforms in order to
articulate, in §2.7, the specific research gap that Sha8lny addresses.

The review is deliberately scoped to the methods that the implemented system
uses or directly competes with, rather than to an exhaustive treatment of every
adjacent field. Where a claim depends on external scholarly literature, a
citation placeholder of the form `[CITATION NEEDED: …]` is inserted; these are
consolidated at the end of the chapter and will be resolved against an
IEEE-formatted reference list. No citations or numerical findings have been
fabricated.

## 2.2 Career Guidance Systems

Career guidance systems aim to help individuals make informed decisions about
occupational direction, skill development, and job search. The field has evolved
from static, questionnaire-based vocational counselling tools toward interactive,
data-driven digital platforms
[CITATION NEEDED: survey of computerized career guidance / vocational counselling
systems].

### 2.2.1 Career recommendation systems

Career recommendation systems suggest occupations or roles to a user based on a
profile of interests, skills, and constraints. A common foundation for such
systems is a structured occupational taxonomy that links jobs to the skills,
tasks, and knowledge they require. The Occupational Information Network (O*NET),
maintained by the United States Department of Labor, is a widely used example of
such a taxonomy and provides occupation-to-skill and occupation-to-task mappings
[CITATION NEEDED: O*NET database / occupational taxonomy reference]. Sha8lny
draws on O*NET data as one input to its knowledge layer, though — as documented
in Chapter 3 — the project uses it as a backend, role-limited proof-of-concept
crosswalk rather than as a comprehensive recommendation backbone.

### 2.2.2 Learning and educational guidance platforms

A second class of systems focuses less on naming a target occupation and more on
guiding the *learning* required to reach it. These systems recommend courses,
resources, or structured learning paths. Their effectiveness depends heavily on
how well they model the learner's current state and target state, a theme
developed further in §2.3. A recurring limitation noted in the literature is that
guidance is frequently generic — calibrated to a global average learner rather
than to a specific regional labour market or an individual's measured skill gaps
[CITATION NEEDED: limitations of generic/one-size-fits-all career guidance].

### 2.2.3 Relevance to Sha8lny

Sha8lny belongs to the data-driven, interactive category of career guidance
systems, but it differs from the typical single-function tool in two respects
that recur throughout this review: it integrates assessment, roadmap generation,
job matching, and advisory into one journey, and it is explicitly grounded in the
Egyptian technology labour market rather than a generic global context.

## 2.3 Personalized Learning Systems

### 2.3.1 Adaptive learning and personalization

Personalized (or adaptive) learning systems tailor educational content and
sequencing to the individual learner rather than presenting a fixed curriculum.
The general principle is to model the learner — their prior knowledge, goals, and
pace — and to use that model to select and order learning activities
[CITATION NEEDED: foundational adaptive learning / personalized learning
reference]. Personalization has been shown in the literature to improve engagement
and learning outcomes relative to undifferentiated instruction
[CITATION NEEDED: empirical evidence on effectiveness of personalized learning].

### 2.3.2 Learning-path generation

Learning-path generation is the sub-problem of producing an ordered sequence of
topics, skills, or resources that moves a learner from their current competence
to a target competence. Approaches range from curated, expert-authored paths
(such as those popularized by community roadmaps) to algorithmically generated
sequences derived from prerequisite graphs or learner models
[CITATION NEEDED: learning-path generation / curriculum sequencing reference].

Sha8lny's roadmap module reflects a hybrid of these approaches. It derives the
*structure* of a learning path from curated, community-maintained roadmap
structures and generates a *personalized* phase-and-milestone plan from the
learner's assessment results using an LLM, while retaining a deterministic,
assessment-aware fallback so that a coherent roadmap is produced even when the
generative model is unavailable. This design directly informs research question
RQ4 (converting formative assessment and skill-gap analysis into personalized
roadmaps).

### 2.3.3 Skill assessment as the input to personalization

The quality of any personalized path depends on the quality of the learner model
that feeds it. Skill assessment in this context is typically *formative* — its
purpose is to diagnose strengths and gaps to guide subsequent learning — rather
than *summative* certification, and it is distinct from formally validated
psychometric instruments, which require established reliability and validity
evidence [CITATION NEEDED: distinction between formative assessment and validated
psychometric testing]. Sha8lny's assessment is explicitly formative and
role/skill-gap oriented; it produces a weighted, per-dimension skill profile to
drive roadmap generation and does not claim psychometric validation. This
positioning is important for the honest framing of the project's contributions.

## 2.4 Recommendation Systems

Recommendation systems are central to both the job-matching and course-matching
components of Sha8lny. The literature distinguishes several classical families of
technique.

### 2.4.1 Content-based filtering

Content-based filtering recommends items whose features match a profile of the
user's preferences or attributes. In a job-matching context, this corresponds to
comparing a user's skills against a job's required skills
[CITATION NEEDED: content-based filtering / content-based recommendation
reference]. Sha8lny uses a content-based foundation: it computes a required-skill
overlap ratio between the user's skill set and each posting's required skills, and
this overlap drives the user-visible match score.

### 2.4.2 Collaborative filtering

Collaborative filtering recommends items based on the behaviour of similar users
(user-user) or co-occurrence patterns among items (item-item), rather than on item
content [CITATION NEEDED: collaborative filtering reference, e.g., matrix
factorization for recommender systems]. A well-known limitation of collaborative
filtering is the *cold-start* problem: it performs poorly when little interaction
history exists for a new user or item [CITATION NEEDED: cold-start problem in
recommender systems]. This limitation is directly relevant to Sha8lny: as a new
platform without a large base of historical user-job interactions, a purely
collaborative approach would be infeasible, which motivates the content-based and
learning-to-rank design described below.

### 2.4.3 Hybrid recommendation and learning-to-rank

Hybrid recommenders combine content-based and collaborative signals, or combine
heuristic features with a learned model, to overcome the weaknesses of any single
approach [CITATION NEEDED: hybrid recommender systems survey]. A practical and
widely used technique for ordering candidate items is *learning-to-rank*, in which
a machine-learning model is trained to optimize the ordering of a list rather than
to predict an absolute score for each item independently
[CITATION NEEDED: learning-to-rank survey, e.g., LambdaMART / listwise ranking].

Sha8lny's job recommender follows exactly this hybrid, learning-to-rank pattern.
Candidate jobs are first filtered and scored by content-based skill overlap, and
the ordering is then refined by a gradient-boosted ranking model (LightGBM)
trained with a `lambdarank` objective and evaluated with ranking metrics such as
Normalized Discounted Cumulative Gain (NDCG) and Mean Average Precision (MAP)
[CITATION NEEDED: LightGBM / gradient boosting decision trees reference]
[CITATION NEEDED: NDCG and MAP ranking-evaluation metrics reference]. Crucially,
and in line with the honesty emphasized throughout this thesis, the ranker is a
**weak-supervision demonstrator**: it is trained on pseudo-labeled synthetic user
profiles over fixture postings and evaluated by leave-one-group-out validation
against skill-overlap and random baselines. Replacing these weak labels with real
labeled Egyptian market data is identified as future work. The system also degrades
gracefully: when no trained model file is present, ranking falls back to the
content-based overlap ordering.

### 2.4.4 Embedding-based semantic matching

Beyond exact skill-token overlap, modern recommenders use dense vector embeddings
to capture *semantic* similarity between text items
[CITATION NEEDED: dense vector representations / sentence embeddings reference,
e.g., Sentence-BERT]. Sha8lny applies this technique to course matching: course
descriptions and skills are embedded with a sentence-transformer model
(`all-MiniLM-L6-v2`) and indexed in a vector store (ChromaDB), enabling
nearest-neighbour retrieval of relevant courses by cosine similarity. This same
embedding-and-retrieval machinery underpins the RAG advisory system discussed in
§2.5.

## 2.5 Artificial Intelligence in Education and Advisory

### 2.5.1 AI tutors, skill assessment, and learning analytics

The application of artificial intelligence to education spans intelligent tutoring
systems, automated skill assessment, and learning analytics that mine learner data
to inform instruction [CITATION NEEDED: survey of AI in education / intelligent
tutoring systems]. Recent advances in large language models have made it feasible
to generate assessment questions, evaluate free-text responses, and produce
conversational guidance at scale [CITATION NEEDED: large language models in
education reference]. Sha8lny uses an LLM (Google Gemini in its default runtime,
with a local Gemma model via Ollama as an offline fallback) for staged assessment
question generation and for the career advisor, while keeping deterministic
fallbacks on every AI path so the system remains demonstrable without network or
API access.

### 2.5.2 Limitations of LLMs: hallucination and grounding

A well-documented limitation of LLMs is their tendency to *hallucinate* —
to generate fluent, confident text that is factually incorrect or unsupported by
any source [CITATION NEEDED: survey on hallucination in large language models].
For a career-advisory application that must give trustworthy, locally accurate
guidance (for example, salary ranges in Egyptian pounds or the names of real
government training programmes), ungrounded generation is a serious liability.
This problem is the central motivation for research question RQ2.

### 2.5.3 Retrieval-augmented generation (RAG)

Retrieval-augmented generation addresses hallucination by retrieving relevant
documents from an external knowledge source and conditioning the model's
generation on that retrieved evidence, rather than relying solely on the model's
parametric memory [CITATION NEEDED: retrieval-augmented generation foundational
reference]. A RAG pipeline typically comprises a document corpus, an embedding
model, a vector index for similarity search, an optional re-ranking stage, and a
generation step that cites or is constrained by the retrieved passages.

Several established information-retrieval techniques strengthen the retrieval
stage, and Sha8lny implements a measured combination of them:

- **Hybrid search** combines dense semantic retrieval with sparse lexical
  retrieval (BM25) so that both paraphrased questions and exact terms (such as
  occupation codes) are matched [CITATION NEEDED: BM25 / probabilistic retrieval
  reference].
- **Reciprocal Rank Fusion (RRF)** merges the dense and lexical result lists into
  a single ranking [CITATION NEEDED: Reciprocal Rank Fusion — Cormack, Clarke, and
  Büttcher, SIGIR 2009 (verify full bibliographic details)].
- **Cross-encoder re-ranking** re-reads the top candidate passages jointly with
  the query for a more accurate final ordering [CITATION NEEDED: passage re-ranking
  with cross-encoders / BERT — Nogueira and Cho, 2019 (verify full bibliographic
  details)].
- **Citation and confidence tiering** returns each passage with its source, URL,
  and a HIGH/MEDIUM/LOW confidence label.
- **An abstention floor** causes the system to return no answer when the retrieved
  evidence is too weak, so the advisor honestly declines rather than fabricating.

This staged, measured pipeline — with a documented baseline and an
attribute-one-technique-at-a-time evaluation — is what distinguishes Sha8lny's
advisory module from a thin wrapper around a commercial LLM API, and it forms the
core of the evaluation reported in Chapter 5.

### 2.5.4 Localization and language

A further limitation relevant to an Egyptian platform is that most widely used
embedding models and knowledge corpora are English-centric, which degrades
retrieval quality for Arabic and code-switched (Arabic-English) queries
[CITATION NEEDED: multilingual / Arabic NLP and embedding reference]. Sha8lny's
current corpus and embedding model are English-centric, and Arabic/code-switched
support is therefore treated as a known limitation and a primary item of future
work rather than a delivered feature.

## 2.6 Existing Platforms

This section analyzes representative existing platforms against which Sha8lny can
be compared. The analysis focuses on publicly observable features; specific
quantitative claims about each platform would require citation and are flagged
accordingly.

### 2.6.1 Coursera

**Features.** A large-scale online course marketplace offering courses,
specializations, and degree/certificate programmes from universities and industry
partners, with structured multi-course pathways
[CITATION NEEDED: Coursera platform description].

**Strengths.** Breadth and credibility of accredited content; structured
specializations; recognized certificates.

**Weaknesses (relative to Sha8lny's goals).** Recommendations are oriented toward
course enrolment rather than toward an individualized, role-targeted career
roadmap grounded in a specific local labour market; it does not match a learner to
local (Egyptian) job openings or surface local salary and government-programme
context.

### 2.6.2 Udemy

**Features.** A broad open marketplace of individually authored courses across
many topics [CITATION NEEDED: Udemy platform description].

**Strengths.** Very large catalogue; affordable, practical, skills-focused
content; frequent updates by individual instructors.

**Weaknesses.** Variable quality due to open authorship; no integrated assessment
→ roadmap → job-matching journey; recommendations are catalogue-centric rather
than career-trajectory-centric and are not localized to the Egyptian market.

### 2.6.3 LinkedIn Learning

**Features.** A professional learning platform integrated with the LinkedIn
professional network and its job listings, offering courses and skill assessments
tied to a user's professional profile [CITATION NEEDED: LinkedIn Learning platform
description].

**Strengths.** Tight coupling between skills, learning content, and a large job
network; profile-driven recommendations.

**Weaknesses.** A commercial, globally oriented ecosystem whose guidance is not
specifically grounded in Egyptian salary data or government training programmes;
its advisory capability is not an evidence-cited, abstaining RAG system; and access
to its full feature set is subscription-gated.

### 2.6.4 roadmap.sh

**Features.** A popular community resource providing curated, visual learning
roadmaps for technology roles (for example, frontend, backend, DevOps)
[CITATION NEEDED: roadmap.sh description].

**Strengths.** High-quality, community-maintained *structure* for what to learn
for a given role, and a clear ordering of topics.

**Weaknesses.** The roadmaps are generic and static — they are not personalized to
an individual's assessed skill gaps, are not connected to job matching or advisory,
and are not localized. **Licensing note:** the roadmap.sh content is made available
under a personal-use-only basis; in Sha8lny it is therefore used strictly as a
development-time structural fallback for roadmap *shape* and is **never cited or
surfaced as a redistributed content source**. This constraint is documented in the
project's dataset registry and is treated as a pre-publication action item.

### 2.6.5 The Egyptian-market gap

None of the platforms above is designed around the Egyptian technology labour
market. They do not surface salary ranges in Egyptian pounds, do not connect
learners to local job postings (such as those aggregated from local job boards),
and do not incorporate official Egyptian resources such as ITIDA/MCIT government
training programmes (DEPI, Train-to-Hire, ITIDA Gigs). This local grounding is a
defining feature of Sha8lny and the basis of research question RQ3
[CITATION NEEDED: ITIDA/MCIT official programme sources — to be supplied].

## 2.7 Research Gap

Synthesizing the preceding sections, the literature and existing platforms reveal
a consistent set of gaps that Sha8lny is designed to close:

1. **Fragmentation.** Existing tools typically address one stage of the
   career-development journey — assessment, *or* learning paths, *or* course
   discovery, *or* job search — without sharing context across stages. There is a
   gap for an *integrated* platform that carries a single learner model through
   assessment → roadmap → progress → job matching → advisory (RQ1).

2. **Ungrounded AI advice.** General-purpose conversational AI answers career
   questions fluently but without evidence, and is prone to hallucination. There is
   a gap for advisory that is grounded in retrieved, cited evidence and that
   abstains when evidence is insufficient (RQ2).

3. **Lack of local grounding.** Mainstream platforms are globally oriented and do
   not incorporate Egypt-specific labour-market data, local salary context, or
   official government training resources (RQ3).

4. **Generic, non-adaptive roadmaps.** Curated roadmaps describe what to learn for
   a role in general but are not personalized to an individual's measured skill
   gaps. There is a gap for converting formative, role-based skill-gap analysis
   into a personalized roadmap (RQ4).

5. **Weak coupling of skills to real opportunities.** Few tools rank actual local
   job postings against an individual's specific skill profile. There is a gap for
   skill-based matching and learning-to-rank over local opportunities (RQ5).

In summary, while individual components — course marketplaces, community roadmaps,
professional networks, and LLM chatbots — exist and are mature, **no widely used
platform integrates them into a single, locally grounded, evidence-cited career
journey for Egyptian technology learners.** This integrated, measured, and honestly
scoped combination is the contribution that Sha8lny sets out to make.

## 2.8 Chapter Summary

This chapter positioned Sha8lny within the literature on career guidance,
personalized learning, recommendation systems, and AI in education. It described
the classical recommendation families (content-based, collaborative, and hybrid
learning-to-rank) that underpin the platform's job and course matching, and the
retrieval-augmented generation techniques (hybrid search, rank fusion,
cross-encoder re-ranking, citation/confidence tiering, and abstention) that
underpin its advisory module. An analysis of Coursera, Udemy, LinkedIn Learning,
and roadmap.sh identified their strengths and their limitations with respect to
integration, AI grounding, local relevance, and personalization. From these
observations, §2.7 articulated a five-part research gap aligned with the project's
research questions. The next chapter, **System Analysis and Design**, translates
this gap into concrete functional and non-functional requirements and presents the
architecture, data model, and AI-engine design that realize the platform.

---

> **Citations required in this chapter (to resolve against the IEEE reference
> list):** computerized career-guidance/vocational systems (§2.2); O*NET
> occupational taxonomy (§2.2.1); limits of generic guidance (§2.2.2); adaptive/
> personalized learning foundations and effectiveness (§2.3.1); learning-path
> generation (§2.3.2); formative vs. psychometric assessment (§2.3.3);
> content-based filtering (§2.4.1); collaborative filtering and cold-start
> (§2.4.2); hybrid recommenders and learning-to-rank/LambdaMART (§2.4.3); LightGBM
> and NDCG/MAP (§2.4.3); sentence embeddings/Sentence-BERT (§2.4.4); AI in
> education / intelligent tutoring (§2.5.1); LLMs in education (§2.5.1); LLM
> hallucination (§2.5.2); RAG foundational paper (§2.5.3); BM25 (§2.5.3);
> Reciprocal Rank Fusion — Cormack et al., SIGIR 2009 (§2.5.3); cross-encoder
> re-ranking — Nogueira & Cho, 2019 (§2.5.3); multilingual/Arabic NLP (§2.5.4);
> platform descriptions for Coursera, Udemy, LinkedIn Learning, roadmap.sh (§2.6);
> ITIDA/MCIT official sources (§2.6.5). **No citation has been fabricated.** Two
> real, well-known references are named for your confirmation (RRF and
> cross-encoder re-ranking) because the codebase itself relies on them; please
> verify and I will format them in IEEE style.
