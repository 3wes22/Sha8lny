"""External taxonomy → curated role/subskill mappings.

These maps declare how external question-bank keys (LinkedIn-style quiz JSON,
generic interview-question CSVs) translate to curated ``(role_key,
subskill_key)`` pairs in the role graph. Adapter scripts
(``scripts/adapt_external_sources.py``, added later) read these maps and emit
``review_status="draft"`` scenarios for human review — nothing here is consumed
at request time.

Every right-hand side must resolve to a real ``(role_key, subskill_key)`` in the
curated role graph; ``tests/test_taxonomy_map.py`` enforces this so a mistyped
mapping fails CI rather than silently dropping content during ingestion.

See ``docs/product/ROLE_GRAPH_METHODOLOGY.md`` for how the curated dimensions,
weights, and subskills are derived.
"""

from __future__ import annotations


# (external_role_slug, external_skill, external_subtopic) -> (role_key, subskill_key)
LINKEDIN_TO_ROLE_GRAPH: dict[tuple[str, str, str], tuple[str, str]] = {
    ("backend-developer", "python", "decorators"): ("backend", "decorators"),
    ("backend-developer", "django", "orm-optimization"): ("backend", "select_related_prefetch"),
    ("backend-developer", "rest", "api-design"): ("backend", "http_api_design"),
    ("backend-developer", "databases", "schema-design"): ("backend", "relational_modeling"),
    ("backend-developer", "architecture", "microservices"): ("backend", "service_decomposition"),
    ("frontend-developer", "javascript", "closures"): ("frontend", "js_closures"),
    ("frontend-developer", "react", "composition"): ("frontend", "component_composition"),
    ("frontend-developer", "react", "hooks"): ("frontend", "hooks_effects"),
    ("frontend-developer", "css", "responsive"): ("frontend", "responsive_css"),
    ("frontend-developer", "html", "accessibility"): ("frontend", "semantic_html"),
    ("data-engineer", "sql", "window-functions"): ("data_science", "window_functions"),
    ("data-engineer", "pipelines", "batch-vs-streaming"): ("data_science", "batch_vs_streaming"),
    ("data-engineer", "modeling", "dimensional"): ("data_science", "star_schema"),
    ("data-engineer", "spark", "fundamentals"): ("data_science", "spark_fundamentals"),
    ("data-engineer", "dbt", "models-and-tests"): ("data_science", "dbt_models"),
}


# external interview-question text -> (role_key, subskill_key)
CSV_TO_ROLE_GRAPH: dict[str, tuple[str, str]] = {
    "What is a Python decorator and when would you use one?": ("backend", "decorators"),
    "How do you avoid N+1 queries in the Django ORM?": ("backend", "select_related_prefetch"),
    "Which HTTP status code should a successful resource creation return?": ("backend", "http_api_design"),
    "How would you normalize a table that repeats customer data?": ("backend", "relational_modeling"),
    "How do you decide where to draw service boundaries in a monolith?": ("backend", "service_decomposition"),
    "Explain how a JavaScript closure captures variables.": ("frontend", "js_closures"),
    "How does the children prop enable component composition in React?": ("frontend", "component_composition"),
    "When does a useEffect run and how do you control it?": ("frontend", "hooks_effects"),
    "How do you write a mobile-first responsive layout in CSS?": ("frontend", "responsive_css"),
    "Why prefer a native button over a clickable div?": ("frontend", "semantic_html"),
    "How do you compute a running total in SQL without grouping rows?": ("data_science", "window_functions"),
    "When would you choose stream processing over batch?": ("data_science", "batch_vs_streaming"),
    "Which table is the fact table in a star schema?": ("data_science", "star_schema"),
    "What triggers execution of a lazy Spark transformation?": ("data_science", "spark_fundamentals"),
    "How do dbt tests enforce primary-key integrity?": ("data_science", "dbt_models"),
    "How do you order Dockerfile steps to reuse the build cache?": ("devops", "dockerfile_best_practices"),
    "Which Kubernetes object performs a rolling update?": ("devops", "k8s_deployments"),
    "How does the bias-variance tradeoff explain overfitting?": ("machine_learning_engineer", "bias_variance"),
    "What causes training/serving skew and how do you prevent it?": ("machine_learning_engineer", "training_serving_skew"),
    "How do you ask a non-leading question in a user interview?": ("ui_ux_designer", "user_interviews"),
}
