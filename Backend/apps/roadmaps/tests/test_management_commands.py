from io import StringIO

import pytest
from django.core.management import call_command

from apps.roadmaps.models import RoadmapTemplate


@pytest.mark.django_db
def test_seed_roadmap_templates_updates_legacy_ui_ux_slug():
    RoadmapTemplate.objects.create(
        title="UI/UX Designer Roadmap",
        slug="ui-ux-designer-roadmap",
        description="Legacy UI/UX roadmap.",
        short_description="Legacy design path",
        target_career="UI/UX Designer",
        career_level=RoadmapTemplate.ENTRY_LEVEL,
        estimated_duration_weeks=16,
        difficulty_level="beginner",
        prerequisites=[],
        learning_outcomes=[],
        is_published=True,
    )

    call_command("seed_roadmap_templates", stdout=StringIO())

    templates = RoadmapTemplate.objects.filter(title="UI/UX Designer Roadmap")
    assert templates.count() == 1
    assert templates.get().slug == "uiux-designer-roadmap"
