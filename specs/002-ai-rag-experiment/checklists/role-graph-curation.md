# Role Graph Curation Checklist

## Reference Policy

- `origin/feature/skill-graph` is an offline reference branch only.
- The mined ESCO/O*NET output is candidate input, not product truth.
- `Backend/apps/assessments/role_graph_data.py` is the sole curated runtime handoff file.

## Curation Rules

- Each supported role uses exactly 4 dimensions.
- Each role contains 15-20 total subskills.
- Each subskill declares `target_proficiency` and same-role `prerequisites`.
- Each role graph starts versioned on day one with `curated-v1`.
- Only the approved roles are curated: `backend`, `frontend`, `data_science`, `fullstack`, `mobile`, `devops`.

## Curated Roles

| Role | Dimensions | Total Subskills | Reference Status |
|------|------------|-----------------|------------------|
| backend | API and Service Design; Data Modeling and Persistence; Reliability and Operations; Delivery and Collaboration | 16 | Curated from hand-picked backend workflow skills |
| frontend | Interface Foundations; Component Architecture; Quality and Performance; Product Delivery | 16 | Curated from hand-picked interface and product execution skills |
| data_science | Data Preparation; Statistics and Experimentation; Modeling and Evaluation; Communication and Delivery | 16 | Curated from hand-picked analysis and modeling skills |
| fullstack | Product Interface Work; API and Service Layer; Data and Integration; Delivery Ownership | 16 | Curated from hand-picked end-to-end product delivery skills |
| mobile | App Foundations; Data and Integration; Native Capabilities; Quality and Release | 16 | Curated from hand-picked mobile execution skills |
| devops | Systems Foundations; Automation and Infrastructure as Code; Observability and Reliability; Security and Collaboration | 16 | Curated from hand-picked platform operations skills |

## Verification Notes

- Runtime code must load curated role graphs through `load_role_graph(...)`.
- Staged assessment caching remains version-bound with `assessment:stage1:{role_key}:{version}`.
- Invalid or incomplete curated graphs must fail explicitly during load.
