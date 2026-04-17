# Role Graph Handoff Contract

## Purpose

This contract isolates role-content curation from workflow implementation. Infrastructure code depends only on the loader API and dataclass shape defined here.

## 1. Integration boundary

Implementation code may import only:

- `SUPPORTED_ROLES`
- `resolve_role_key(target_career: str) -> str`
- `load_role_graph(role_key: str) -> RoleGraph`

The curated-content handoff edits only:

- `Backend/apps/assessments/role_graph_data.py`

## 2. Dataclass contract

### `SubSkill`

| Field | Required | Rules |
|------|----------|-------|
| `key` | Yes | Unique within role graph |
| `label` | Yes | Human-readable |
| `dimension` | Yes | Must match parent dimension key |
| `target_proficiency` | Yes | Integer 1-5 |
| `prerequisites` | Yes | List of subskill keys within same role graph |

### `CoreDimension`

| Field | Required | Rules |
|------|----------|-------|
| `key` | Yes | Unique within role graph |
| `label` | Yes | Human-readable |
| `weight` | Yes | Numeric, role total must sum to 1.0 |
| `subskills` | Yes | 3-6 subskills |

### `RoleGraph`

| Field | Required | Rules |
|------|----------|-------|
| `role_key` | Yes | One of supported roles |
| `role_label` | Yes | Human-readable |
| `dimensions` | Yes | 3-5 dimensions |
| `version` | Yes | Bump on any semantic content change |

## 3. Supported roles

Initial required keys:

- `backend`
- `frontend`
- `data_science`
- `fullstack`
- `mobile`
- `devops`

## 4. Stub-to-curated replacement rules

- Stub data must be structurally valid from day one.
- Curated data replaces stub entries in the same `ROLE_GRAPHS` mapping.
- No other file changes are required when curated data lands.
- Changing `version` invalidates cached stage-one question sets for that role.
- Stage-one cache keys use the pattern `assessment:stage1:{role_key}:{version}`.
- Local development defaults to `DJANGO_CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache`, so the cache requires no external setup.

## 5. Validation expectations

Loader validation must reject:

- missing supported role keys
- weights that do not sum to `1.0`
- duplicate dimension or subskill keys
- prerequisite references that do not resolve
- target proficiency values outside `1-5`

## 6. Consumer guarantees

Assessment engine, question generation, cache keys, serializers, and tests must depend on this contract rather than on raw inline dictionaries.
