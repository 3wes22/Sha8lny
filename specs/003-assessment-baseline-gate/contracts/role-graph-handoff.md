# Role Graph Handoff Contract

## Purpose

This contract isolates role-content curation from workflow implementation and defines the curated role-graph expectations that the current working-tree candidate must satisfy before it becomes baseline.

## 1. Integration boundary

Implementation code may import only:

- `SUPPORTED_ROLES`
- `resolve_role_key(target_career: str) -> str`
- `load_role_graph(role_key: str) -> RoleGraph`

The curated-content handoff edits only:

- `Backend/apps/assessments/role_graph_data.py`

## 2. Reference policy

- `origin/feature/skill-graph` is an offline reference branch only.
- Mined ESCO or O*NET output is candidate input, not product truth.
- `Backend/apps/assessments/role_graph_data.py` is the sole curated runtime handoff file.

## 3. Dataclass contract

### `SubSkill`

| Field | Required | Rules |
|------|----------|-------|
| `key` | Yes | Unique within role graph |
| `label` | Yes | Human-readable |
| `dimension` | Yes | Must match parent dimension key |
| `target_proficiency` | Yes | Integer `1-5` |
| `prerequisites` | Yes | List of subskill keys within the same role graph |

### `CoreDimension`

| Field | Required | Rules |
|------|----------|-------|
| `key` | Yes | Unique within role graph |
| `label` | Yes | Human-readable |
| `weight` | Yes | Numeric; role total must sum to `1.0` |
| `subskills` | Yes | `4-5` subskills for the curated baseline |

### `RoleGraph`

| Field | Required | Rules |
|------|----------|-------|
| `role_key` | Yes | One of the supported roles |
| `role_label` | Yes | Human-readable |
| `dimensions` | Yes | Exactly `4` dimensions for the curated baseline |
| `version` | Yes | Bump on any semantic content change |

## 4. Supported roles

Required mapping keys:

- `backend`
- `frontend`
- `data_science`
- `fullstack`
- `mobile`
- `devops`

## 5. Curated baseline rules

- Each supported role uses exactly `4` dimensions.
- Each role contains `15-20` total subskills.
- Each subskill declares `target_proficiency` and same-role `prerequisites`.
- Curated day-one baseline version is `curated-v1`.
- The mapping key must match `RoleGraph.role_key`.
- Invalid or incomplete curated graphs must fail explicitly during load.

## 6. Cache and replacement rules

- Curated data replaces prior content in the same `ROLE_GRAPHS` mapping.
- No runtime file outside `role_graph_data.py` should require edits for content-only curation changes.
- Changing `version` invalidates cached stage-one question sets for that role.
- Stage-one cache keys use the pattern `assessment:stage1:{role_key}:{version}`.

## 7. Validation expectations

Loader validation must reject:

- missing supported role keys
- mapping keys that do not match `RoleGraph.role_key`
- weights that do not sum to `1.0`
- duplicate dimension or subskill keys
- prerequisite references that do not resolve
- target proficiency values outside `1-5`

## 8. Consumer guarantees

Assessment generation, stage-one cache keys, deterministic scoring, roadmap-signal output, and tests all depend on this contract rather than on raw inline dictionaries.

## 9. Baseline review assertions

The current working-tree candidate can only become baseline if:

- every supported role loads successfully through `load_role_graph(...)`
- curated replacement is version-aware and cache-safe
- the loader reports invalid graphs explicitly rather than silently degrading
- downstream recommendation and roadmap behavior continues to derive from the same curated graph
