from __future__ import annotations

from apps.assessments.role_graph import CoreDimension, RoleGraph, SubSkill


def skill(
    key: str,
    label: str,
    dimension: str,
    target_proficiency: int,
    prerequisites: list[str] | None = None,
) -> SubSkill:
    return SubSkill(
        key=key,
        label=label,
        dimension=dimension,
        target_proficiency=target_proficiency,
        prerequisites=prerequisites or [],
    )


def dimension(
    key: str,
    label: str,
    weight: float,
    subskills: list[SubSkill],
) -> CoreDimension:
    return CoreDimension(
        key=key,
        label=label,
        weight=weight,
        subskills=subskills,
    )


ROLE_GRAPHS = {
    "backend": RoleGraph(
        role_key="backend",
        role_label="Backend Developer",
        version="stub-v1",
        dimensions=[
            dimension(
                "technical_depth",
                "Core Backend Skills",
                0.24,
                [
                    skill("api_design", "REST API Design", "technical_depth", 4),
                    skill("database_modeling", "Database Modeling", "technical_depth", 4, ["api_design"]),
                    skill("auth_flows", "Authentication Flows", "technical_depth", 4, ["api_design"]),
                ],
            ),
            dimension(
                "tooling",
                "Backend Tooling",
                0.20,
                [
                    skill("orm_usage", "ORM Usage", "tooling", 4, ["database_modeling"]),
                    skill("testing_backend", "Backend Testing", "tooling", 4, ["api_design"]),
                    skill("deployment_basics", "Deployment Basics", "tooling", 3, ["testing_backend"]),
                ],
            ),
            dimension(
                "problem_solving",
                "Debugging and Reasoning",
                0.20,
                [
                    skill("log_analysis", "Log Analysis", "problem_solving", 4),
                    skill("performance_debugging", "Performance Debugging", "problem_solving", 3, ["log_analysis"]),
                    skill("incident_triage", "Incident Triage", "problem_solving", 3, ["log_analysis"]),
                ],
            ),
            dimension(
                "experience",
                "Project Execution",
                0.18,
                [
                    skill("service_architecture", "Service Architecture", "experience", 4, ["api_design"]),
                    skill("data_migrations", "Data Migrations", "experience", 3, ["database_modeling"]),
                    skill("production_delivery", "Production Delivery", "experience", 3, ["deployment_basics"]),
                ],
            ),
            dimension(
                "collaboration",
                "Collaboration and Quality",
                0.18,
                [
                    skill("code_review", "Code Review", "collaboration", 3),
                    skill("documentation", "Technical Documentation", "collaboration", 3),
                    skill("requirement_translation", "Requirement Translation", "collaboration", 3, ["documentation"]),
                ],
            ),
        ],
    ),
    "frontend": RoleGraph(
        role_key="frontend",
        role_label="Frontend Developer",
        version="stub-v1",
        dimensions=[
            dimension(
                "technical_depth",
                "Core Frontend Skills",
                0.24,
                [
                    skill("semantic_html", "Semantic HTML", "technical_depth", 4),
                    skill("responsive_css", "Responsive CSS", "technical_depth", 4, ["semantic_html"]),
                    skill("component_state", "Component State", "technical_depth", 4),
                ],
            ),
            dimension(
                "tooling",
                "Framework Tooling",
                0.20,
                [
                    skill("react_patterns", "React Patterns", "tooling", 4, ["component_state"]),
                    skill("typescript_frontend", "TypeScript", "tooling", 4, ["react_patterns"]),
                    skill("frontend_testing", "Frontend Testing", "tooling", 3, ["react_patterns"]),
                ],
            ),
            dimension(
                "problem_solving",
                "UI Debugging",
                0.20,
                [
                    skill("browser_debugging", "Browser Debugging", "problem_solving", 4),
                    skill("performance_tuning", "Performance Tuning", "problem_solving", 3, ["browser_debugging"]),
                    skill("state_diagnosis", "State Diagnosis", "problem_solving", 4, ["component_state"]),
                ],
            ),
            dimension(
                "experience",
                "Product Delivery",
                0.18,
                [
                    skill("design_translation", "Design Translation", "experience", 4),
                    skill("api_integration", "API Integration", "experience", 4, ["react_patterns"]),
                    skill("accessibility_review", "Accessibility Review", "experience", 3, ["semantic_html"]),
                ],
            ),
            dimension(
                "collaboration",
                "Frontend Collaboration",
                0.18,
                [
                    skill("design_systems", "Design Systems", "collaboration", 3, ["design_translation"]),
                    skill("cross_functional_alignment", "Cross-functional Alignment", "collaboration", 3),
                    skill("frontend_documentation", "Frontend Documentation", "collaboration", 3),
                ],
            ),
        ],
    ),
    "data_science": RoleGraph(
        role_key="data_science",
        role_label="Data Scientist",
        version="stub-v1",
        dimensions=[
            dimension(
                "technical_depth",
                "Core Data Skills",
                0.24,
                [
                    skill("python_analysis", "Python Analysis", "technical_depth", 4),
                    skill("statistics", "Statistics", "technical_depth", 4),
                    skill("feature_engineering", "Feature Engineering", "technical_depth", 4, ["python_analysis"]),
                ],
            ),
            dimension(
                "tooling",
                "Modeling Tooling",
                0.20,
                [
                    skill("notebook_workflows", "Notebook Workflows", "tooling", 3),
                    skill("sklearn_modeling", "Scikit-learn Modeling", "tooling", 4, ["statistics"]),
                    skill("experiment_tracking", "Experiment Tracking", "tooling", 3, ["sklearn_modeling"]),
                ],
            ),
            dimension(
                "problem_solving",
                "Analytical Reasoning",
                0.20,
                [
                    skill("hypothesis_testing", "Hypothesis Testing", "problem_solving", 4, ["statistics"]),
                    skill("data_quality", "Data Quality Diagnosis", "problem_solving", 4, ["python_analysis"]),
                    skill("model_debugging", "Model Debugging", "problem_solving", 3, ["sklearn_modeling"]),
                ],
            ),
            dimension(
                "experience",
                "Project Execution",
                0.18,
                [
                    skill("storytelling", "Data Storytelling", "experience", 4),
                    skill("ml_projects", "ML Project Delivery", "experience", 3, ["feature_engineering"]),
                    skill("stakeholder_reporting", "Stakeholder Reporting", "experience", 3, ["storytelling"]),
                ],
            ),
            dimension(
                "collaboration",
                "Operational Readiness",
                0.18,
                [
                    skill("dataset_documentation", "Dataset Documentation", "collaboration", 3),
                    skill("metric_alignment", "Metric Alignment", "collaboration", 3),
                    skill("handoff_readiness", "Handoff Readiness", "collaboration", 3, ["dataset_documentation"]),
                ],
            ),
        ],
    ),
    "fullstack": RoleGraph(
        role_key="fullstack",
        role_label="Full Stack Developer",
        version="stub-v1",
        dimensions=[
            dimension(
                "technical_depth",
                "Cross-stack Fundamentals",
                0.24,
                [
                    skill("ui_implementation", "UI Implementation", "technical_depth", 4),
                    skill("api_delivery", "API Delivery", "technical_depth", 4),
                    skill("data_flow", "End-to-end Data Flow", "technical_depth", 4, ["ui_implementation", "api_delivery"]),
                ],
            ),
            dimension(
                "tooling",
                "Full-stack Tooling",
                0.20,
                [
                    skill("frontend_state", "Frontend State Management", "tooling", 4, ["ui_implementation"]),
                    skill("backend_testing", "Backend Testing", "tooling", 3, ["api_delivery"]),
                    skill("deployment_pipeline", "Deployment Pipeline", "tooling", 3, ["data_flow"]),
                ],
            ),
            dimension(
                "problem_solving",
                "Integration Debugging",
                0.20,
                [
                    skill("integration_debugging", "Integration Debugging", "problem_solving", 4, ["data_flow"]),
                    skill("performance_reasoning", "Performance Reasoning", "problem_solving", 3, ["integration_debugging"]),
                    skill("failure_isolation", "Failure Isolation", "problem_solving", 3, ["integration_debugging"]),
                ],
            ),
            dimension(
                "experience",
                "Delivery Experience",
                0.18,
                [
                    skill("product_slicing", "Product Slicing", "experience", 4),
                    skill("auth_end_to_end", "Auth End-to-end", "experience", 3, ["api_delivery"]),
                    skill("portfolio_apps", "Portfolio Apps", "experience", 3, ["data_flow"]),
                ],
            ),
            dimension(
                "collaboration",
                "Execution Hygiene",
                0.18,
                [
                    skill("testing_strategy", "Testing Strategy", "collaboration", 3),
                    skill("handoff_clarity", "Handoff Clarity", "collaboration", 3),
                    skill("quality_checks", "Quality Checks", "collaboration", 3, ["testing_strategy"]),
                ],
            ),
        ],
    ),
    "mobile": RoleGraph(
        role_key="mobile",
        role_label="Mobile Developer",
        version="stub-v1",
        dimensions=[
            dimension(
                "technical_depth",
                "Core Mobile Skills",
                0.24,
                [
                    skill("mobile_ui", "Mobile UI Layout", "technical_depth", 4),
                    skill("navigation", "Navigation Flows", "technical_depth", 4, ["mobile_ui"]),
                    skill("state_management_mobile", "Mobile State Management", "technical_depth", 4, ["navigation"]),
                ],
            ),
            dimension(
                "tooling",
                "Mobile Tooling",
                0.20,
                [
                    skill("api_sync_mobile", "API Sync", "tooling", 4),
                    skill("local_storage_mobile", "Local Storage", "tooling", 3),
                    skill("mobile_testing", "Mobile Testing", "tooling", 3, ["navigation"]),
                ],
            ),
            dimension(
                "problem_solving",
                "Runtime Debugging",
                0.20,
                [
                    skill("device_debugging", "Device Debugging", "problem_solving", 4),
                    skill("performance_mobile", "Performance Profiling", "problem_solving", 3, ["device_debugging"]),
                    skill("platform_edge_cases", "Platform Edge Cases", "problem_solving", 3, ["device_debugging"]),
                ],
            ),
            dimension(
                "experience",
                "App Delivery",
                0.18,
                [
                    skill("app_release", "App Release Flow", "experience", 3),
                    skill("offline_behavior", "Offline Behavior", "experience", 3, ["local_storage_mobile"]),
                    skill("mobile_project_scope", "Mobile Project Scope", "experience", 4),
                ],
            ),
            dimension(
                "collaboration",
                "Quality and Handoff",
                0.18,
                [
                    skill("qa_feedback", "QA Feedback Handling", "collaboration", 3),
                    skill("analytics_instrumentation", "Analytics Instrumentation", "collaboration", 3),
                    skill("release_notes", "Release Notes", "collaboration", 3, ["app_release"]),
                ],
            ),
        ],
    ),
    "devops": RoleGraph(
        role_key="devops",
        role_label="DevOps Engineer",
        version="stub-v1",
        dimensions=[
            dimension(
                "technical_depth",
                "Infrastructure Fundamentals",
                0.24,
                [
                    skill("linux_operations", "Linux Operations", "technical_depth", 4),
                    skill("networking_basics", "Networking Basics", "technical_depth", 4),
                    skill("cloud_compute", "Cloud Compute", "technical_depth", 4, ["linux_operations"]),
                ],
            ),
            dimension(
                "tooling",
                "Automation Tooling",
                0.20,
                [
                    skill("containerization", "Containerization", "tooling", 4, ["linux_operations"]),
                    skill("ci_cd", "CI/CD Pipelines", "tooling", 4, ["containerization"]),
                    skill("infra_as_code", "Infrastructure as Code", "tooling", 4, ["cloud_compute"]),
                ],
            ),
            dimension(
                "problem_solving",
                "Reliability Response",
                0.20,
                [
                    skill("incident_response", "Incident Response", "problem_solving", 4),
                    skill("observability", "Observability", "problem_solving", 4),
                    skill("capacity_reasoning", "Capacity Reasoning", "problem_solving", 3, ["observability"]),
                ],
            ),
            dimension(
                "experience",
                "Operational Delivery",
                0.18,
                [
                    skill("release_coordination", "Release Coordination", "experience", 3, ["ci_cd"]),
                    skill("environment_strategy", "Environment Strategy", "experience", 3, ["infra_as_code"]),
                    skill("security_basics", "Security Basics", "experience", 3, ["linux_operations"]),
                ],
            ),
            dimension(
                "collaboration",
                "Platform Collaboration",
                0.18,
                [
                    skill("runbooks", "Runbooks", "collaboration", 3),
                    skill("incident_communication", "Incident Communication", "collaboration", 3, ["incident_response"]),
                    skill("developer_enablement", "Developer Enablement", "collaboration", 3, ["ci_cd"]),
                ],
            ),
        ],
    ),
}
