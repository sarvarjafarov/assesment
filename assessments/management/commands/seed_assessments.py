from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from assessments.models import Assessment, Choice, Question, RoleCategory

SEED_DATA = [
    {
        "category": {
            "name": "General Behaviors",
            "slug": "general-behaviors",
            "summary": "Measure collaboration habits, decision making, and adaptability.",
            "icon": "users",
        },
        "assessments": [
            {
                "title": "Behavioral Readiness Index",
                "slug": "behavioral-readiness",
                "summary": "Scenario-neutral behavioral inventory covering communication, adaptability, and integrity.",
                "level": "intro",
                "duration_minutes": 18,
                "skills_focus": [
                    "Communication",
                    "Adaptability",
                    "Problem Solving",
                    "Teamwork",
                    "Integrity",
                ],
                "scoring_rubric": {
                    "behavioral_weight_profile": "general_behaviors",
                    "dimensions": [
                        "Communication",
                        "Adaptability",
                        "Problem Solving",
                        "Teamwork",
                        "Integrity",
                    ],
                },
                "questions": [
                    {
                        "order": 1,
                        "prompt": "Select the statements that are most and least like you for each set.",
                        "question_type": "behavioral",
                        "metadata": {
                            "behavioral_bank": {
                                "dataset": "default",
                                "blocks": list(range(1, 51)),
                            }
                        },
                    }
                ],
            }
        ],
    }
]


class Command(BaseCommand):
    help = "Seed the database with default assessment categories, assessments, and questions."

    @transaction.atomic
    def handle(self, *args, **options):
        desired_category_slugs = [entry["category"]["slug"] for entry in SEED_DATA]
        desired_assessment_slugs = [
            assessment["slug"]
            for entry in SEED_DATA
            for assessment in entry["assessments"]
        ]
        Assessment.objects.exclude(slug__in=desired_assessment_slugs).delete()
        RoleCategory.objects.exclude(slug__in=desired_category_slugs).delete()
        for entry in SEED_DATA:
            category_payload = entry["category"]
            category, created = RoleCategory.objects.update_or_create(
                slug=category_payload["slug"],
                defaults={
                    "name": category_payload["name"],
                    "summary": category_payload.get("summary", ""),
                    "icon": category_payload.get("icon", ""),
                    "is_active": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} category {category.name}"))

            for assessment_payload in entry["assessments"]:
                question_payloads = assessment_payload["questions"]
                assessment, assessment_created = Assessment.objects.update_or_create(
                    slug=assessment_payload["slug"],
                    defaults={
                        "category": category,
                        "title": assessment_payload["title"],
                        "summary": assessment_payload["summary"],
                        "level": assessment_payload.get("level", "intro"),
                        "duration_minutes": assessment_payload.get(
                            "duration_minutes", 20
                        ),
                        "skills_focus": assessment_payload.get("skills_focus", []),
                        "scoring_rubric": assessment_payload.get("scoring_rubric", {}),
                        "is_active": True,
                    },
                )
                self.stdout.write(
                    f" - {'Created' if assessment_created else 'Updated'} assessment {assessment.title}"
                )

                for q_payload in question_payloads:
                    choices = q_payload.get("choices", [])
                    defaults = {
                        "prompt": q_payload["prompt"],
                        "question_type": q_payload.get("question_type", "single"),
                        "metadata": q_payload.get("metadata", {}),
                        "weight": q_payload.get("weight", 1.0),
                    }
                    question, question_created = Question.objects.update_or_create(
                        assessment=assessment,
                        order=q_payload.get("order", 1),
                        defaults=defaults,
                    )

                    self.stdout.write(
                        f"    · {'Created' if question_created else 'Updated'} question {question.order}"
                    )

                    if choices:
                        for choice_payload in choices:
                            Choice.objects.update_or_create(
                                question=question,
                                label=choice_payload["label"],
                                defaults={
                                    "value": choice_payload.get("value", ""),
                                    "weight": choice_payload.get("weight", 1.0),
                                },
                            )
        self.stdout.write(self.style.SUCCESS("Seeding completed."))
