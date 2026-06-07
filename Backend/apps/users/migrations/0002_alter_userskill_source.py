from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userskill",
            name="source",
            field=models.CharField(
                choices=[
                    ("user_input", "User Input"),
                    ("assessment", "Assessment"),
                    ("roadmap_milestone", "Roadmap Milestone"),
                    ("verified", "Verified"),
                ],
                default="user_input",
                help_text="Source of skill data",
                max_length=50,
            ),
        ),
    ]
