"""
Assessment taxonomy metadata and RoleGraph builders.

All assessment_weight / min_questions_per_stage values live here and are applied
to role_graph_data ROLE_GRAPHS via build_role_graph_from_taxonomy().
"""

from __future__ import annotations

from typing import Any

from apps.assessments.role_graph import CoreDimension, RoleGraph, SubSkill


def _dim(
    key: str,
    label: str,
    assessment_weight: float,
    min_questions: int,
    subskill_specs: list[tuple[str, str, int]],
    *,
    origin: str | None = None,
) -> CoreDimension:
    subskills = [
        SubSkill(
            key=sk_key,
            label=sk_label,
            dimension=key,
            target_proficiency=prof,
            prerequisites=[],
            frame="debugging" if "debugging" in key else None,
        )
        for sk_key, sk_label, prof in subskill_specs
    ]
    structural = assessment_weight
    return CoreDimension(
        key=key,
        label=label,
        weight=structural,
        subskills=subskills,
        assessment_weight=assessment_weight,
        min_questions_per_stage=min_questions,
        origin=origin or None,
    )


# --- Frontend (11 dimensions) ---
FRONTEND_TAXONOMY: dict[str, dict[str, Any]] = {
    "html_accessibility": {
        "label": "HTML and Accessibility",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("semantic_html", "Semantic HTML", 4),
            ("accessibility_fundamentals", "Accessibility Fundamentals", 4),
            ("aria_patterns", "ARIA Patterns", 3),
            ("document_outline", "Document Outline", 3),
        ],
    },
    "css_layout_styling": {
        "label": "CSS Layout and Styling",
        "weight": 0.10,
        "min": 2,
        "subskills": [
            ("responsive_css", "Responsive CSS", 4),
            ("css_grid_flexbox", "CSS Grid and Flexbox", 4),
            ("css_specificity", "CSS Specificity", 3),
            ("design_tokens", "Design Tokens", 3),
        ],
    },
    "javascript_fundamentals": {
        "label": "JavaScript Fundamentals",
        "weight": 0.15,
        "min": 3,
        "subskills": [
            ("js_closures", "Closures and Scope", 4),
            ("js_async", "Async/Await and Promises", 4),
            ("js_event_loop", "Event Loop", 4),
            ("js_prototypes", "Prototypes and `this`", 3),
        ],
    },
    "react_core": {
        "label": "React Core",
        "weight": 0.15,
        "min": 2,
        "subskills": [
            ("component_composition", "Component Composition", 4),
            ("react_rendering", "Rendering and Reconciliation", 4),
            ("react_state_basics", "Component State Basics", 4),
            ("react_context", "Context API", 3),
        ],
    },
    "react_hooks_depth": {
        "label": "React Hooks Depth",
        "weight": 0.10,
        "min": 2,
        "subskills": [
            ("hooks_effects", "useEffect Patterns", 4),
            ("hooks_memoization", "useMemo and useCallback", 4),
            ("hooks_custom", "Custom Hooks", 4),
            ("hooks_rules", "Rules of Hooks", 3),
        ],
    },
    "state_management": {
        "label": "State Management",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("redux_patterns", "Redux Patterns", 4),
            ("server_state", "Server State (React Query)", 4),
            ("local_vs_global", "Local vs Global State", 3),
            ("state_colocation", "State Colocation", 3),
        ],
    },
    "performance_optimization": {
        "label": "Performance Optimization",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("rendering_performance", "Rendering Performance", 4),
            ("bundle_splitting", "Code Splitting", 3),
            ("lazy_loading", "Lazy Loading", 3),
            ("web_vitals", "Core Web Vitals", 3),
        ],
    },
    "debugging_devtools": {
        "label": "Debugging and DevTools",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("browser_debugging", "Browser Debugging", 4),
            ("network_panel", "Network Panel", 3),
            ("react_devtools", "React DevTools", 3),
            ("source_maps", "Source Maps", 3),
        ],
    },
    "typescript_basics": {
        "label": "TypeScript Basics",
        "weight": 0.07,
        "min": 1,
        "subskills": [
            ("typescript_frontend", "TypeScript for Frontend", 4),
            ("typing_props", "Typing Component Props", 3),
            ("union_types", "Union and Discriminated Unions", 3),
            ("generic_components", "Generic Components", 3),
        ],
    },
    "testing": {
        "label": "Frontend Testing",
        "weight": 0.06,
        "min": 1,
        "subskills": [
            ("frontend_testing", "Frontend Testing", 4),
            ("testing_library", "Testing Library", 3),
            ("mocking_fetch", "Mocking API Calls", 3),
            ("snapshot_tradeoffs", "Snapshot Test Tradeoffs", 3),
        ],
    },
    "security_basics": {
        "label": "Frontend Security Basics",
        "weight": 0.05,
        "min": 1,
        "subskills": [
            ("xss_prevention", "XSS Prevention", 4),
            ("csrf_basics", "CSRF Basics", 3),
            ("secure_storage", "Token Storage", 3),
            ("csp_basics", "Content Security Policy", 3),
        ],
    },
}

# --- Backend ---
BACKEND_TAXONOMY: dict[str, dict[str, Any]] = {
    "python_fundamentals": {
        "label": "Python Fundamentals",
        "weight": 0.12,
        "min": 2,
        "subskills": [
            ("decorators", "Decorators", 4),
            ("generators", "Generators", 4),
            ("context_managers", "Context Managers", 3),
            ("type_hints", "Type Hints", 3),
        ],
    },
    "django_orm": {
        "label": "Django ORM",
        "weight": 0.12,
        "min": 2,
        "subskills": [
            ("select_related_prefetch", "select_related / prefetch_related", 4),
            ("queryset_optimization", "QuerySet Optimization", 4),
            ("migrations", "Migrations", 3),
            ("custom_managers", "Custom Managers", 3),
        ],
    },
    "rest_api_design": {
        "label": "REST API Design",
        "weight": 0.10,
        "min": 2,
        "subskills": [
            ("http_api_design", "HTTP API Design", 4),
            ("drf_serializers", "DRF Serializers", 4),
            ("idempotency", "Idempotency", 3),
            ("pagination_filtering", "Pagination and Filtering", 3),
        ],
    },
    "database_design": {
        "label": "Database Design",
        "weight": 0.10,
        "min": 1,
        "subskills": [
            ("relational_modeling", "Relational Modeling", 4),
            ("query_optimization", "Query Optimization", 4),
            ("indexing_strategy", "Indexing Strategy", 3),
            ("transactions", "Transactions", 3),
        ],
    },
    "authentication_security": {
        "label": "Authentication and Security",
        "weight": 0.09,
        "min": 1,
        "subskills": [
            ("auth_authorization", "Authentication and Authorization", 4),
            ("jwt_vs_session", "JWT vs Session", 3),
            ("sql_injection_prevention", "SQL Injection Prevention", 4),
            ("rate_limiting", "Rate Limiting", 3),
        ],
    },
    "async_and_task_queues": {
        "label": "Async and Task Queues",
        "weight": 0.09,
        "min": 1,
        "subskills": [
            ("async_workflows", "Asynchronous Workflows", 4),
            ("celery_task_design", "Celery Task Design", 4),
            ("idempotent_tasks", "Idempotent Tasks", 3),
            ("redis_broker", "Redis as Broker", 3),
        ],
    },
    "caching_strategy": {
        "label": "Caching Strategy",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("caching_patterns", "Caching Patterns", 4),
            ("cache_invalidation", "Cache Invalidation", 3),
            ("django_cache_framework", "Django Cache Framework", 3),
            ("redis_data_structures", "Redis Data Structures", 3),
        ],
    },
    "system_design_fundamentals": {
        "label": "System Design Fundamentals",
        "weight": 0.10,
        "min": 1,
        "subskills": [
            ("service_decomposition", "Service Decomposition", 4),
            ("scalability_patterns", "Scalability Patterns", 3),
            ("load_balancing", "Load Balancing", 3),
            ("event_driven_basics", "Event-Driven Basics", 3),
        ],
    },
    "testing": {
        "label": "Backend Testing",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("backend_testing_strategy", "Backend Testing Strategy", 4),
            ("pytest_fixtures", "pytest Fixtures", 3),
            ("django_test_client", "Django Test Client", 3),
            ("mocking_patching", "Mocking and Patching", 3),
        ],
    },
    "debugging_and_observability": {
        "label": "Debugging and Observability",
        "weight": 0.07,
        "min": 1,
        "subskills": [
            ("logging_monitoring", "Logging and Monitoring", 4),
            ("performance_debugging", "Performance Debugging", 4),
            ("structured_logging", "Structured Logging", 3),
            ("slow_query_log", "Slow Query Log", 3),
        ],
    },
    "python_packaging_and_tooling": {
        "label": "Python Packaging and Tooling",
        "weight": 0.05,
        "min": 1,
        "subskills": [
            ("virtual_environments", "Virtual Environments", 3),
            ("requirements_pinning", "Requirements Pinning", 3),
            ("linting_formatting", "Linting and Formatting", 3),
            ("pyproject_toml", "pyproject.toml", 3),
        ],
    },
}

DEVOPS_TAXONOMY: dict[str, dict[str, Any]] = {
    "containerization": {"label": "Containerization", "weight": 0.13, "min": 2, "subskills": [
        ("dockerfile_best_practices", "Dockerfile Best Practices", 4),
        ("multi_stage_builds", "Multi-stage Builds", 4),
        ("docker_compose", "Docker Compose", 3),
        ("container_networking", "Container Networking", 3),
    ]},
    "kubernetes": {"label": "Kubernetes", "weight": 0.13, "min": 2, "subskills": [
        ("k8s_deployments", "Deployments and Services", 4),
        ("configmap_secret", "ConfigMaps and Secrets", 4),
        ("hpa_basics", "Horizontal Pod Autoscaler", 3),
        ("ingress_basics", "Ingress Controllers", 3),
    ]},
    "ci_cd_pipelines": {"label": "CI/CD Pipelines", "weight": 0.12, "min": 2, "subskills": [
        ("pipeline_as_code", "Pipeline as Code", 4),
        ("deployment_gates", "Deployment Gates", 3),
        ("rollback_strategy", "Rollback Strategy", 3),
        ("secrets_in_ci", "Secrets in CI", 4),
    ]},
    "infrastructure_as_code": {"label": "Infrastructure as Code", "weight": 0.11, "min": 1, "subskills": [
        ("terraform_modules", "Terraform Modules", 4),
        ("terraform_state", "Terraform State", 3),
        ("drift_detection", "Drift Detection", 3),
        ("idempotent_apply", "Idempotent Apply", 3),
    ]},
    "cloud_fundamentals": {"label": "Cloud Fundamentals", "weight": 0.10, "min": 1, "subskills": [
        ("iam_least_privilege", "IAM Least Privilege", 4),
        ("vpc_subnets", "VPC and Subnets", 3),
        ("load_balancer_types", "Load Balancer Types", 3),
        ("object_storage", "Object Storage", 3),
    ]},
    "observability_and_monitoring": {"label": "Observability", "weight": 0.10, "min": 1, "subskills": [
        ("metrics_logs_traces", "Metrics, Logs, Traces", 4),
        ("slo_error_budget", "SLO and Error Budget", 3),
        ("alerting_strategy", "Alerting Strategy", 3),
        ("on_call_runbooks", "On-call Runbooks", 3),
    ]},
    "networking": {"label": "Networking", "weight": 0.08, "min": 1, "subskills": [
        ("dns_tls", "DNS and TLS", 4),
        ("network_policies", "Network Policies", 3),
        ("ingress_egress", "Ingress/Egress Control", 3),
        ("service_mesh_basics", "Service Mesh Basics", 3),
    ]},
    "security_and_compliance": {"label": "Security and Compliance", "weight": 0.09, "min": 1, "subskills": [
        ("secrets_management", "Secrets Management", 4),
        ("image_scanning", "Image Scanning", 3),
        ("sast_dast", "SAST/DAST in Pipeline", 3),
        ("audit_logging", "Audit Logging", 3),
    ]},
    "reliability_and_incident_management": {
        "label": "Reliability and Incidents",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("incident_runbooks", "Incident Runbooks", 4),
            ("blue_green_canary", "Blue/Green and Canary", 3),
            ("postmortem", "Blameless Postmortems", 3),
            ("chaos_basics", "Chaos Engineering Basics", 3),
        ],
    },
    "scripting_and_automation": {"label": "Scripting and Automation", "weight": 0.06, "min": 1, "subskills": [
        ("bash_scripting", "Bash Scripting", 3),
        ("python_for_ops", "Python for Ops", 3),
        ("idempotent_scripts", "Idempotent Scripts", 3),
        ("cron_vs_events", "Cron vs Event-driven", 3),
    ]},
}

DATA_ENGINEER_TAXONOMY: dict[str, dict[str, Any]] = {
    "sql_and_query_optimization": {"label": "SQL and Query Optimization", "weight": 0.14, "min": 2, "subskills": [
        ("window_functions", "Window Functions", 4),
        ("query_execution_plan", "Query Execution Plans", 4),
        ("indexing_analytics", "Indexing for Analytics", 3),
        ("ctes", "CTEs", 3),
    ]},
    "data_pipeline_design": {"label": "Data Pipeline Design", "weight": 0.13, "min": 2, "subskills": [
        ("batch_vs_streaming", "Batch vs Streaming", 4),
        ("idempotent_pipelines", "Idempotent Pipelines", 4),
        ("backfill_strategy", "Backfill Strategy", 3),
        ("late_arriving_data", "Late-arriving Data", 3),
    ]},
    "data_modeling": {"label": "Data Modeling", "weight": 0.11, "min": 1, "subskills": [
        ("star_schema", "Star Schema", 4),
        ("scd", "Slowly Changing Dimensions", 3),
        ("normalization_tradeoffs", "Normalization Tradeoffs", 3),
        ("surrogate_keys", "Surrogate Keys", 3),
    ]},
    "distributed_data_processing": {"label": "Distributed Processing", "weight": 0.10, "min": 1, "subskills": [
        ("spark_fundamentals", "Spark Fundamentals", 4),
        ("partitioning_strategy", "Partitioning Strategy", 3),
        ("shuffle_ops", "Shuffle Operations", 3),
        ("broadcast_join", "Broadcast Join", 3),
    ]},
    "data_warehouse_and_lakehouse": {"label": "Warehouse and Lakehouse", "weight": 0.10, "min": 1, "subskills": [
        ("dbt_models", "dbt Models and Tests", 4),
        ("medallion_architecture", "Medallion Architecture", 3),
        ("columnar_storage", "Columnar Storage", 3),
        ("time_travel", "Time Travel Queries", 3),
    ]},
    "streaming_and_messaging": {"label": "Streaming and Messaging", "weight": 0.09, "min": 1, "subskills": [
        ("kafka_consumer_groups", "Kafka Consumer Groups", 4),
        ("offset_management", "Offset Management", 3),
        ("dead_letter_queue", "Dead Letter Queue", 3),
        ("schema_registry", "Schema Registry", 3),
    ]},
    "data_quality_and_testing": {"label": "Data Quality", "weight": 0.09, "min": 1, "subskills": [
        ("data_contracts", "Data Contracts", 4),
        ("schema_validation", "Schema Validation", 3),
        ("null_monitoring", "Null Rate Monitoring", 3),
        ("dbt_tests", "dbt Tests", 3),
    ]},
    "python_for_data": {"label": "Python for Data", "weight": 0.08, "min": 1, "subskills": [
        ("pandas_vectorization", "pandas Vectorization", 4),
        ("chunked_processing", "Chunked Processing", 3),
        ("memory_optimization", "Memory Optimization", 3),
        ("type_casting", "Type Casting Strategy", 3),
    ]},
    "orchestration": {"label": "Orchestration", "weight": 0.01, "min": 1, "subskills": [
        ("airflow_dag_design", "Airflow DAG Design", 4),
        ("task_dependencies", "Task Dependencies", 3),
        ("sensors_triggers", "Sensors vs Triggers", 3),
        ("idempotent_tasks", "Idempotent Tasks", 3),
    ]},
    "storage_and_formats": {"label": "Storage and Formats", "weight": 0.09, "min": 1, "subskills": [
        ("parquet_vs_json", "Parquet vs JSON", 4),
        ("partitioning_storage", "Object Storage Partitioning", 3),
        ("small_file_problem", "Small File Problem", 3),
        ("schema_evolution", "Schema Evolution", 3),
    ]},
    "debugging_data_pipelines": {
        "label": "Debugging Data Pipelines",
        "weight": 0.06,
        "min": 1,
        "subskills": [
            ("pipeline_failure_diagnosis", "Pipeline Failure Diagnosis", 4),
            ("data_quality_triage", "Data Quality Triage", 3),
            ("schema_mismatch_debug", "Schema Mismatch Debugging", 3),
            ("backfill_failure", "Backfill Failure Analysis", 3),
        ],
    },
}

ML_ENGINEER_TAXONOMY: dict[str, dict[str, Any]] = {
    "ml_fundamentals": {"label": "ML Fundamentals", "weight": 0.12, "min": 2, "subskills": [
        ("bias_variance", "Bias-Variance Tradeoff", 4),
        ("cross_validation", "Cross Validation", 4),
        ("evaluation_metrics", "Evaluation Metrics", 3),
        ("data_leakage", "Data Leakage", 4),
    ]},
    "model_training_and_experimentation": {"label": "Model Training", "weight": 0.11, "min": 1, "subskills": [
        ("hyperparameter_tuning", "Hyperparameter Tuning", 4),
        ("early_stopping", "Early Stopping", 3),
        ("experiment_tracking", "Experiment Tracking", 3),
        ("reproducibility", "Reproducibility", 3),
    ]},
    "ml_system_design": {"label": "ML System Design", "weight": 0.12, "min": 2, "subskills": [
        ("training_serving_skew", "Training/Serving Skew", 4),
        ("feature_store", "Feature Store", 3),
        ("model_versioning", "Model Versioning", 3),
        ("ab_testing_models", "A/B Testing Models", 3),
    ]},
    "model_deployment_and_serving": {"label": "Model Deployment", "weight": 0.11, "min": 1, "subskills": [
        ("model_serving", "Model Serving", 4),
        ("batching_inference", "Batching for Throughput", 3),
        ("latency_accuracy", "Latency vs Accuracy", 3),
        ("containerizing_models", "Containerizing Models", 3),
    ]},
    "mlops_and_pipelines": {"label": "MLOps", "weight": 0.10, "min": 1, "subskills": [
        ("ml_pipelines", "ML Pipelines", 4),
        ("model_registry", "Model Registry", 3),
        ("drift_detection", "Drift Detection", 3),
        ("retraining_triggers", "Retraining Triggers", 3),
    ]},
    "llm_and_rag": {"label": "LLM and RAG", "weight": 0.10, "min": 1, "subskills": [
        ("prompt_engineering", "Prompt Engineering", 4),
        ("rag_retrieval", "RAG Retrieval Strategy", 4),
        ("chunking_strategies", "Chunking Strategies", 3),
        ("hallucination_mitigation", "Hallucination Mitigation", 3),
    ]},
    "python_ml_ecosystem": {"label": "Python ML Ecosystem", "weight": 0.09, "min": 1, "subskills": [
        ("sklearn_pipeline", "sklearn Pipeline", 4),
        ("numpy_vectorization", "NumPy Vectorization", 3),
        ("pytorch_basics", "PyTorch Basics", 3),
        ("gpu_utilization", "GPU Utilization", 3),
    ]},
    "data_preprocessing": {"label": "Data Preprocessing", "weight": 0.08, "min": 1, "subskills": [
        ("feature_scaling", "Feature Scaling", 3),
        ("encoding_categoricals", "Encoding Categoricals", 3),
        ("class_imbalance", "Class Imbalance", 4),
        ("train_test_split", "Train/Val/Test Split", 3),
    ]},
    "monitoring_and_observability": {"label": "ML Monitoring", "weight": 0.09, "min": 1, "subskills": [
        ("prediction_drift", "Prediction Drift", 4),
        ("data_drift", "Data Drift", 3),
        ("performance_degradation", "Performance Degradation", 3),
        ("shadow_scoring", "Shadow Scoring", 3),
    ]},
    "debugging_ml_systems": {
        "label": "Debugging ML Systems",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("error_analysis", "Error Analysis", 4),
            ("confusion_matrix", "Confusion Matrix", 3),
            ("learning_curves", "Learning Curves", 3),
            ("inference_profiling", "Inference Profiling", 3),
        ],
    },
}

MOBILE_TAXONOMY: dict[str, dict[str, Any]] = {
    "react_native_fundamentals": {"label": "React Native Fundamentals", "weight": 0.13, "min": 2, "subskills": [
        ("rn_architecture", "RN Architecture", 4),
        ("stylesheet_rn", "StyleSheet in RN", 3),
        ("flatlist_perf", "FlatList Performance", 4),
        ("platform_specific", "Platform-specific Code", 3),
    ]},
    "react_core_for_mobile": {"label": "React Core for Mobile", "weight": 0.11, "min": 2, "subskills": [
        ("hooks_mobile", "Hooks in Mobile", 4),
        ("navigation_state", "Navigation State", 3),
        ("memo_mobile", "Memoization on Mobile", 3),
        ("deep_linking", "Deep Linking", 3),
    ]},
    "mobile_performance": {"label": "Mobile Performance", "weight": 0.12, "min": 1, "subskills": [
        ("js_ui_thread", "JS vs UI Thread", 4),
        ("hermes_engine", "Hermes Engine", 3),
        ("image_caching", "Image Caching", 3),
        ("reanimated_basics", "Reanimated Basics", 3),
    ]},
    "navigation": {"label": "Navigation", "weight": 0.09, "min": 1, "subskills": [
        ("stack_tab_drawer", "Stack/Tab/Drawer", 4),
        ("navigation_params", "Navigation Params", 3),
        ("auth_flow_nav", "Auth Flow Navigation", 3),
        ("screen_options", "Screen Options", 3),
    ]},
    "device_apis_and_permissions": {"label": "Device APIs", "weight": 0.08, "min": 1, "subskills": [
        ("permissions_flow", "Permission Flow", 4),
        ("camera_storage", "Camera and Storage", 3),
        ("push_notifications", "Push Notifications", 3),
        ("biometric_auth", "Biometric Auth", 3),
    ]},
    "offline_and_data_sync": {"label": "Offline and Sync", "weight": 0.09, "min": 1, "subskills": [
        ("async_storage", "AsyncStorage vs MMKV", 3),
        ("optimistic_updates", "Optimistic Updates", 4),
        ("network_state", "Network State", 3),
        ("react_query_mobile", "React Query Mobile", 3),
    ]},
    "testing_mobile": {"label": "Mobile Testing", "weight": 0.08, "min": 1, "subskills": [
        ("jest_rn", "Jest RN Mocking", 3),
        ("detox_e2e", "Detox E2E", 3),
        ("component_testing", "Component Testing", 3),
        ("native_module_mock", "Native Module Mocking", 3),
    ]},
    "release_and_distribution": {"label": "Release", "weight": 0.08, "min": 1, "subskills": [
        ("ota_updates", "OTA Updates", 3),
        ("app_signing", "App Signing", 3),
        ("fastlane_basics", "Fastlane Basics", 3),
        ("store_submission", "Store Submission", 3),
    ]},
    "accessibility_mobile": {"label": "Mobile Accessibility", "weight": 0.07, "min": 1, "subskills": [
        ("accessibility_label", "accessibilityLabel", 3),
        ("screen_reader", "Screen Reader Testing", 3),
        ("touch_targets", "Touch Target Sizing", 3),
        ("color_contrast", "Color Contrast", 3),
    ]},
    "debugging_mobile": {
        "label": "Debugging Mobile",
        "weight": 0.08,
        "min": 1,
        "subskills": [
            ("flipper", "Flipper", 4),
            ("metro_errors", "Metro Error Reading", 3),
            ("native_crash", "Native Crash Symbolication", 3),
            ("perf_monitor", "Performance Monitor", 3),
        ],
    },
    "typescript_in_rn": {"label": "TypeScript in RN", "weight": 0.07, "min": 1, "subskills": [
        ("typing_nav_params", "Typing Nav Params", 3),
        ("prop_types", "Component Prop Types", 3),
        ("api_typing", "API Response Typing", 3),
        ("generic_components", "Generic Components", 3),
    ]},
}

FULLSTACK_EXTRA: dict[str, dict[str, Any]] = {
    "api_contract_design": {
        "label": "API Contract Design",
        "weight": 0.04,
        "min": 1,
        "origin": "fullstack",
        "subskills": [
            ("rest_vs_graphql", "REST vs GraphQL", 4),
            ("openapi_schema", "OpenAPI Schema", 3),
            ("cors_configuration", "CORS Configuration", 3),
            ("error_standards", "Error Response Standards", 3),
        ],
    },
    "full_stack_debugging": {
        "label": "Full Stack Debugging",
        "weight": 0.03,
        "min": 1,
        "origin": "fullstack",
        "subskills": [
            ("network_tab_debug", "Network Tab Inspection", 4),
            ("cors_errors", "CORS Errors", 3),
            ("auth_token_flow", "Auth Token Flow", 3),
            ("db_to_ui_trace", "DB to UI Trace", 3),
        ],
    },
    "deployment_and_environments": {
        "label": "Deployment and Environments",
        "weight": 0.03,
        "min": 1,
        "origin": "fullstack",
        "subskills": [
            ("env_variables", "Environment Variables", 3),
            ("static_serving", "Static File Serving", 3),
            ("reverse_proxy", "Reverse Proxy", 3),
            ("twelve_factor", "12-Factor Basics", 3),
        ],
    },
}

ROLE_TAXONOMIES: dict[str, dict[str, dict[str, Any]]] = {
    "frontend": FRONTEND_TAXONOMY,
    "backend": BACKEND_TAXONOMY,
    "devops": DEVOPS_TAXONOMY,
    "data_science": DATA_ENGINEER_TAXONOMY,
    "machine_learning_engineer": ML_ENGINEER_TAXONOMY,
    "android": MOBILE_TAXONOMY,
}

FRONTEND_DIMENSION_KEYS = frozenset(FRONTEND_TAXONOMY.keys())
BACKEND_DIMENSION_KEYS = frozenset(BACKEND_TAXONOMY.keys())


def get_taxonomy(role_key: str) -> dict[str, dict[str, Any]] | None:
    if role_key == "fullstack":
        return _build_fullstack_taxonomy()
    return ROLE_TAXONOMIES.get(role_key)


def get_all_role_keys() -> list[str]:
    from apps.assessments.role_graph import SUPPORTED_ROLES

    return list(SUPPORTED_ROLES)


def get_all_required_dimensions(role_graph: RoleGraph) -> list[str]:
    return [dimension.key for dimension in role_graph.dimensions if dimension.min_questions_per_stage >= 1]


def is_debugging_dimension(dimension_key: str) -> bool:
    return "debugging" in dimension_key


def _prefix_subskills(prefix: str, subskills: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    return [(f"{prefix}_{sk}", label, prof) for sk, label, prof in subskills]


def _build_fullstack_taxonomy() -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for key, spec in FRONTEND_TAXONOMY.items():
        entry = dict(spec)
        entry["weight"] = round(spec["weight"] * 0.45, 4)
        entry["origin"] = "frontend"
        entry["subskills"] = _prefix_subskills("fe", spec["subskills"])
        merged[f"fe_{key}"] = entry
    for key, spec in BACKEND_TAXONOMY.items():
        entry = dict(spec)
        entry["weight"] = round(spec["weight"] * 0.45, 4)
        entry["origin"] = "backend"
        entry["subskills"] = _prefix_subskills("be", spec["subskills"])
        merged[f"be_{key}"] = entry
    for key, spec in FULLSTACK_EXTRA.items():
        merged[key] = dict(spec)
    total = sum(item["weight"] for item in merged.values())
    if abs(total - 1.0) > 1e-3:
        factor = 1.0 / total
        for entry in merged.values():
            entry["weight"] = round(entry["weight"] * factor, 4)
    return merged


def build_role_graph_from_taxonomy(
    *,
    role_key: str,
    role_label: str,
    taxonomy: dict[str, dict[str, Any]],
    version: str,
) -> RoleGraph:
    total_weight = sum(float(spec["weight"]) for spec in taxonomy.values())
    normalize = abs(total_weight - 1.0) > 1e-3
    dimensions: list[CoreDimension] = []
    for key, spec in taxonomy.items():
        weight = float(spec["weight"])
        if normalize:
            weight = round(weight / total_weight, 4)
        dimensions.append(
            _dim(
                key,
                spec["label"],
                weight,
                int(spec["min"]),
                spec["subskills"],
                origin=spec.get("origin"),
            )
        )
    weight_drift = 1.0 - sum(dimension.weight for dimension in dimensions)
    if dimensions and abs(weight_drift) > 1e-9:
        last = dimensions[-1]
        dimensions[-1] = CoreDimension(
            key=last.key,
            label=last.label,
            weight=round(last.weight + weight_drift, 6),
            subskills=last.subskills,
            assessment_weight=last.assessment_weight,
            min_questions_per_stage=last.min_questions_per_stage,
            origin=last.origin,
        )

    return RoleGraph(
        role_key=role_key,
        role_label=role_label,
        dimensions=dimensions,
        version=version,
    )
