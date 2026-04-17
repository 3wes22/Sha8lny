from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0003_assessment_ai_task_id_assessment_ai_trace_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="assessment",
            name="generation_metadata",
            field=models.JSONField(blank=True, default=dict, help_text="Trace, cache, fallback, and validation metadata for staged assessments"),
        ),
        migrations.AddField(
            model_name="assessment",
            name="gap_profile",
            field=models.JSONField(blank=True, default=dict, help_text="Intermediate gap analysis for staged assessments"),
        ),
        migrations.AddField(
            model_name="assessment",
            name="roadmap_signal",
            field=models.JSONField(blank=True, default=dict, help_text="Final roadmap-ready signal for staged assessments"),
        ),
        migrations.AddField(
            model_name="assessment",
            name="stage",
            field=models.CharField(blank=True, choices=[("stage_1", "Stage 1"), ("stage_2", "Stage 2"), ("completed", "Completed")], help_text="Current staged assessment phase for new skills assessments", max_length=32),
        ),
        migrations.AddField(
            model_name="assessment",
            name="stage_one_questions",
            field=models.JSONField(blank=True, default=list, help_text="Generated stage-one questions for staged assessments"),
        ),
        migrations.AddField(
            model_name="assessment",
            name="stage_one_responses",
            field=models.JSONField(blank=True, default=list, help_text="Submitted stage-one responses for staged assessments"),
        ),
        migrations.AddField(
            model_name="assessment",
            name="stage_two_questions",
            field=models.JSONField(blank=True, default=list, help_text="Generated stage-two questions for staged assessments"),
        ),
        migrations.AddField(
            model_name="assessment",
            name="stage_two_responses",
            field=models.JSONField(blank=True, default=list, help_text="Submitted stage-two responses for staged assessments"),
        ),
        migrations.AddField(
            model_name="assessmentresult",
            name="roadmap_signal",
            field=models.JSONField(blank=True, default=dict, help_text="Structured roadmap-ready staged assessment signal"),
        ),
    ]
