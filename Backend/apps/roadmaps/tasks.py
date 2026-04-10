"""
Celery tasks for async roadmap generation.
"""

from __future__ import annotations

import logging

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from apps.core.ai_logging import log_ai_failure
from apps.core.ai_settings import AI_TASK_HARD_TIME_LIMIT, AI_TASK_SOFT_TIME_LIMIT
from apps.roadmaps.models import Roadmap
from apps.roadmaps.services import RoadmapService

logger = logging.getLogger(__name__)


def run_generate_ai_roadmap(roadmap_id: str, *, task_id: str | None = None) -> str:
    roadmap = Roadmap.objects.select_related("assessment", "user", "template").get(
        id=roadmap_id,
        is_deleted=False,
    )
    try:
        RoadmapService.populate_ai_roadmap(roadmap, task_id=task_id)
    except (SoftTimeLimitExceeded, Exception) as error:
        roadmap.refresh_from_db()
        RoadmapService.record_generation_failure(
            roadmap,
            error_message=str(error),
            error_code=type(error).__name__,
        )
        generation = roadmap.metadata.get("generation", {}) if isinstance(roadmap.metadata, dict) else {}
        log_ai_failure(
            feature="roadmap_generation",
            error=error,
            trace_id=str(generation.get("trace_id") or roadmap.id),
            extra={"roadmap_id": str(roadmap.id), "task_id": task_id},
        )
        raise
    return roadmap_id


@shared_task(
    bind=True,
    name="apps.roadmaps.generate_ai_roadmap",
    soft_time_limit=AI_TASK_SOFT_TIME_LIMIT,
    time_limit=AI_TASK_HARD_TIME_LIMIT,
)
def generate_ai_roadmap_task(self, roadmap_id: str) -> str:
    return run_generate_ai_roadmap(roadmap_id, task_id=self.request.id)
