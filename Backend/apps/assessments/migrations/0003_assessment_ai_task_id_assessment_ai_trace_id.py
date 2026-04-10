from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0002_assessment_target_career"),
    ]

    operations = [
        migrations.AddField(
            model_name="assessment",
            name="ai_task_id",
            field=models.CharField(blank=True, help_text="Celery task ID for question generation or evaluation", max_length=255),
        ),
        migrations.AddField(
            model_name="assessment",
            name="ai_trace_id",
            field=models.CharField(blank=True, help_text="Trace ID for the latest AI invocation", max_length=64),
        ),
    ]
