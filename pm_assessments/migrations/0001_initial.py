from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProductQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("question_text", models.TextField()),
                (
                    "question_type",
                    models.CharField(
                        choices=[
                            ("multiple_choice", "Multiple choice"),
                            ("scenario", "Scenario based"),
                            ("ranking", "Ranking / Ordering"),
                            ("behavioral_most", "Behavioral - most like me"),
                            ("behavioral_least", "Behavioral - least like me"),
                            ("reasoning", "Reasoning / open response"),
                        ],
                        max_length=32,
                    ),
                ),
                ("difficulty_level", models.PositiveSmallIntegerField(default=3)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("strategy", "Product strategy"),
                            ("roadmap", "Roadmap & prioritization"),
                            ("discovery", "Research & discovery"),
                            ("analytics", "Analytics & experiments"),
                            ("delivery", "Execution & delivery"),
                            ("stakeholder", "Stakeholder collaboration"),
                            ("behavioral", "Behavioral"),
                        ],
                        max_length=32,
                    ),
                ),
                ("options", models.JSONField(blank=True, default=dict)),
                ("correct_answer", models.JSONField(blank=True, null=True)),
                ("scoring_weight", models.DecimalField(decimal_places=2, default=1.0, max_digits=5)),
                ("explanation", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ("category", "-created_at")},
        ),
        migrations.CreateModel(
            name="ProductAssessmentSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("candidate_id", models.CharField(db_index=True, max_length=120)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("in_progress", "In progress"), ("submitted", "Submitted")],
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("question_set", models.JSONField(default=list)),
                ("responses", models.JSONField(blank=True, default=list)),
                ("hard_skill_score", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("soft_skill_score", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("overall_score", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("category_breakdown", models.JSONField(blank=True, default=dict)),
                ("recommendations", models.JSONField(blank=True, default=dict)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("duration_minutes", models.PositiveIntegerField(default=30)),
            ],
            options={
                "ordering": ("-created_at",),
                "indexes": [models.Index(fields=["candidate_id"], name="pm_assessm_candida_idx")],
            },
        ),
    ]
