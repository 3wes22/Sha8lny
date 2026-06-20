# Visual Assets — Master List (All Chapters)

> **Purpose.** A single, authoritative inventory of every figure, table, diagram, chart, and
> screenshot in the thesis, with the **exact caption** and **placement** for each. Use it to
> (a) build the List of Figures / List of Tables, (b) track which assets still need to be
> produced, and (c) keep captions consistent. Numbering follows `Chapter.Index`.
>
> **Production tips.** Architectural/UML/DFD diagrams: author in Mermaid (already embedded in
> the chapter files) or draw.io/PlantUML and export to SVG/PNG at ≥ 300 dpi. Charts: generate
> from the evaluation data (e.g., Matplotlib) so they are reproducible. Screenshots: capture at
> a consistent viewport (e.g., 1440×900), light theme, with realistic but non-sensitive data.

---

## Figures

| Figure | Type | Caption | Chapter / placement | Source |
|--------|------|---------|---------------------|--------|
| 1.1 | Concept diagram | The skills-mismatch loop in the Egyptian technology labour market. | §1.1.1 | Draw |
| 1.2 | Timeline | Evolution of career-guidance technology toward retrieval-grounded LLM systems. | §1.1.2 | Draw |
| 1.3 | Block diagram | Sha8lny at a glance: four integrated services around one competency profile. | §1.1.3 / §1.7 | Draw |
| 2.1 | PRISMA flow | Literature selection flow: records identified, screened, and included. | §2.1 | Draw |
| 2.2 | Pipeline diagram | A canonical retrieval-augmented generation pipeline. | §2.2.2 | Draw |
| 2.3 | Taxonomy tree | Taxonomy of AI techniques employed in Sha8lny. | §2.2 | Draw |
| 2.4 | Positioning diagram | Positioning of Sha8lny relative to prior work. | §2.5 | Draw |
| 3.1 | Architecture | High-level system architecture of Sha8lny. | §3.3.1 | Mermaid (in file) |
| 3.2 | Component diagram | Component architecture: backend modules and AI package. | §3.3.2 | Mermaid (in file) |
| 3.3 | Flowchart | Primary end-to-end user workflow. | §3.3.3 | Mermaid (in file) |
| 3.4 | DFD L0 | Context diagram. | §3.5.1 | Mermaid (in file) |
| 3.5 | DFD L1 | Major-process data-flow diagram. | §3.5.2 | Mermaid (in file) |
| 3.6 | DFD L2 | Assessment process expanded. | §3.5.3 | Mermaid (in file) |
| 3.7 | Use-case diagram | System use cases and actors. | §3.6.1 | Mermaid (in file) |
| 3.8 | Class diagram | Domain class diagram. | §3.6.2 | Mermaid (in file) |
| 3.9 | Activity diagram | "Take Assessment" activity flow. | §3.6.3 | Draw/PlantUML |
| 3.10 | Sequence diagram | Submit assessment and receive result. | §3.6.4 | Mermaid (in file) |
| 3.11 | State diagram | Assessment lifecycle states. | §3.6.5 | Mermaid (in file) |
| 3.12 | Deployment diagram | Production deployment topology. | §3.6.6 | Mermaid (in file) |
| 4.1 | ERD | Entity-Relationship Diagram of the Sha8lny database. | §4.3.2 | draw.io |
| 4.2 | Sequence/flow | API request lifecycle with JWT and async AI. | §4.4.3 | Draw |
| 4.5 | Pipeline | Two-stage assessment pipeline. | §4.2.3 | Reuse Fig. 3.6 |
| 4.6 | Screenshot | Landing page presenting the Sha8lny value proposition. | §4.6.3 | Capture (`/`) |
| 4.7 | Screenshot | Authentication screens (login / register). | §4.6.3 | Capture |
| 4.8 | Screenshot | Career-atlas dashboard with progress snapshot. | §4.6.3 | Capture (`/dashboard`) |
| 4.9 | Screenshot | Career-path selection across eight roles. | §4.6.3 | Capture (`/assessment`) |
| 4.10 | Screenshot | Adaptive question card with progress rail. | §4.6.3 | Capture (session) |
| 4.11 | Screenshot | Competency result with strengths and gaps. | §4.6.3 | Capture (results) |
| 4.12 | Screenshot | Personalised roadmap with AI source panel. | §4.6.3 | Capture (`/roadmap`) |
| 4.13 | Screenshot | Skill-matched jobs with match explanation. | §4.6.3 | Capture (`/jobs`) |
| 4.14 | Screenshot | Grounded advisor chat showing cited sources. | §4.6.3 | Capture (`/advisor`) |
| 4.15 | Screenshot | Profile, skills, and preferences. | §4.6.3 | Capture (`/profile`) |
| 5.1 | Diagram | Testing pyramid applied to Sha8lny. | §5.1 | Draw |
| 5.2 | Bar chart | Job-ranker NDCG@5/@10 vs. overlap and random baselines. | §5.4.1 | Generate from eval |
| 5.3 | Bar chart | Retrieval recall@5 / MRR: hybrid+rerank vs. dense-only. | §5.4.2 | Generate from eval |
| 5.4 | Chart | API latency distribution by endpoint class. | §5.4.3 | Generate from load test |
| 6.1 | Diagram | Sha8lny positioned against prior work (explainability, locality, integration). | §6.4 | Draw |
| 7.1 | Roadmap timeline | Short-, long-term, and research future work. | §7.2 | Draw |

## Tables

| Table | Caption | Chapter / placement |
|-------|---------|---------------------|
| 1.1 | Specific, measurable objectives and their success criteria. | §1.4.2 |
| 1.2 | Project scope: included vs. excluded features. | §1.5 |
| 2.1 | Comparison matrix of related work and systems. | §2.4 |
| 2.2 | Research-gap analysis. | §2.5 |
| 3.1 | Functional requirements. | §3.2.2 |
| 3.2 | Non-functional requirements. | §3.2.3 |
| 3.3 | Key design decisions and trade-offs. | §3.4 |
| 4.1 | Development and target hardware. | §4.1.1 |
| 4.2 | Core technology stack and versions. | §4.1.2 |
| 4.3 | Selected core database tables. | §4.3.3 |
| 4.4 | Representative API endpoints. | §4.4.2 |
| 4.5 | Security controls mapped to threats. | §4.5 |
| 4.6 | Screens and recommended screenshots. | §4.6.3 |
| 5.1 | Test suite summary. | §5.1 |
| 5.2 | UAT scenarios. | §5.1.4 |
| 5.4 | Job-ranker evaluation (leave-one-group-out CV). | §5.4.1 |
| 5.5 | Retrieval quality on the 55-query evaluation set. | §5.4.2 |
| 5.6 | Latency and throughput (reference host). | §5.4.3 |
| 5.7 | Resource utilisation under moderate load. | §5.4.4 |
| 6.1 | Validation of contributions against evidence. | §6.3 |
| 7.1 | Objectives and outcomes. | §7.1.1 |
| 7.2 | Future-work roadmap mapped to limitations. | §7.2 |
| D.1 | Representative test cases. | Appendix D |

## Asset production checklist

- [ ] All Mermaid diagrams exported to SVG/PNG and embedded with captions.
- [ ] ERD (Fig. 4.1) drawn in draw.io and exported.
- [ ] All 10 UI screenshots (Figs. 4.6–4.15) captured at a consistent viewport.
- [ ] Charts 5.2–5.4 generated from the committed evaluation outputs.
- [ ] Every figure/table referenced at least once in the body text ("see Figure x.y").
- [ ] List of Figures and List of Tables regenerated after final numbering.
