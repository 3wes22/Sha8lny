"""
Partial O*NET 30.1 crosswalk for Backend Developer milestones.

Element IDs and task statements are taken from
``ai-models/data/onet_data/db_30_1_text/Content Model Reference.txt``.
Only the backend role is mapped in v1 (depth over breadth).
"""

from __future__ import annotations

from typing import Any


ONET_ONLINE_BASE = "https://www.onetonline.org/find/descriptor/browse/"

# Verified against Content Model Reference.txt (O*NET 30.1)
BACKEND_ONET_MAP: dict[str, dict[str, Any]] = {
    "rest api": {
        "onet_element_id": "2.B.4.g",
        "onet_title": "Systems Analysis",
        "onet_task": "Determining how a system should work and how changes in conditions, operations, and the environment will affect outcomes.",
        "confidence": 0.82,
    },
    "api": {
        "onet_element_id": "2.B.4.g",
        "onet_title": "Systems Analysis",
        "onet_task": "Determining how a system should work and how changes in conditions, operations, and the environment will affect outcomes.",
        "confidence": 0.80,
    },
    "programming": {
        "onet_element_id": "2.B.3.e",
        "onet_title": "Programming",
        "onet_task": "Writing computer programs for various purposes.",
        "confidence": 0.90,
    },
    "python": {
        "onet_element_id": "2.B.3.e",
        "onet_title": "Programming",
        "onet_task": "Writing computer programs for various purposes.",
        "confidence": 0.88,
    },
    "database": {
        "onet_element_id": "2.B.4.g",
        "onet_title": "Systems Analysis",
        "onet_task": "Determining how a system should work and how changes in conditions, operations, and the environment will affect outcomes.",
        "confidence": 0.78,
    },
    "sql": {
        "onet_element_id": "2.B.4.g",
        "onet_title": "Systems Analysis",
        "onet_task": "Determining how a system should work and how changes in conditions, operations, and the environment will affect outcomes.",
        "confidence": 0.76,
    },
    "authentication": {
        "onet_element_id": "2.B.3.b",
        "onet_title": "Technology Design",
        "onet_task": "Generating or adapting equipment and technology to serve user needs.",
        "confidence": 0.75,
    },
    "testing": {
        "onet_element_id": "2.B.3.m",
        "onet_title": "Quality Control Analysis",
        "onet_task": "Conducting tests and inspections of products, services, or processes to evaluate quality or performance.",
        "confidence": 0.84,
    },
    "debug": {
        "onet_element_id": "2.B.3.k",
        "onet_title": "Troubleshooting",
        "onet_task": "Determining causes of operating errors and deciding what to do about it.",
        "confidence": 0.83,
    },
    "deploy": {
        "onet_element_id": "2.B.4.h",
        "onet_title": "Systems Evaluation",
        "onet_task": "Identifying measures or indicators of system performance and the actions needed to improve or correct performance, relative to the goals of the system.",
        "confidence": 0.77,
    },
}


def onet_resource(entry: dict[str, Any]) -> dict[str, str]:
    element_id = entry["onet_element_id"]
    return {
        "title": f"O*NET: {entry['onet_title']}",
        "url": f"{ONET_ONLINE_BASE}{element_id}/",
        "type": "onet",
        "onet_element_id": element_id,
    }


class RoadmapONETMapper:
    """Map milestone titles to O*NET references for the backend role."""

    @staticmethod
    def map_milestone(milestone_title: str, role_key: str) -> list[dict[str, Any]]:
        if role_key != "backend":
            return []

        normalized = milestone_title.lower()
        mappings: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for keyword, entry in BACKEND_ONET_MAP.items():
            if keyword not in normalized:
                continue
            element_id = entry["onet_element_id"]
            if element_id in seen_ids:
                continue
            seen_ids.add(element_id)
            mappings.append(
                {
                    "milestone_title": milestone_title,
                    "onet_element_id": element_id,
                    "onet_title": entry["onet_title"],
                    "onet_task": entry["onet_task"],
                    "confidence": entry["confidence"],
                    "resource": onet_resource(entry),
                }
            )
        return mappings
