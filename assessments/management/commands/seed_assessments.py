from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from assessments.models import Assessment, Choice, Question, RoleCategory

SEED_DATA = [
    {
        "category": {
            "name": "Digital Marketing",
            "slug": "digital-marketing",
            "summary": "Evaluate paid media, lifecycle automation, and analytics readiness.",
            "icon": "sparkles",
        },
        "assessments": [
            {
                "title": "Digital Marketing Fundamentals",
                "slug": "digital-marketing-fundamentals",
                "summary": "Measures campaign planning, channel mastery, and data fluency.",
                "level": "intermediate",
                "duration_minutes": 30,
                "skills_focus": ["Paid Ads", "Lifecycle", "Analytics"],
                "scoring_rubric": {"tiers": ["Emerging", "Ready", "Expert"]},
                "questions": [
                    {
                        "order": 1,
                        "prompt": "Which KPI best demonstrates paid social efficiency when budgets fluctuate weekly?",
                        "question_type": "single",
                        "choices": [
                            {"label": "Click-through rate", "weight": 0.5},
                            {"label": "Cost per incremental lift", "weight": 1.0},
                            {"label": "Reach", "weight": 0.3},
                        ],
                    },
                    {
                        "order": 2,
                        "prompt": "Select the automations you would deploy for a new product onboarding journey.",
                        "question_type": "multi",
                        "choices": [
                            {"label": "Behavior-triggered nurture", "weight": 0.6},
                            {"label": "Time-based announcement", "weight": 0.3},
                            {"label": "Win-back for disengaged cohort", "weight": 0.6},
                        ],
                    },
                    {
                        "order": 3,
                        "prompt": "Rate your confidence in building a multi-touch attribution dashboard.",
                        "question_type": "scale",
                        "metadata": {"scale_labels": ["Low", "Medium", "High"]},
                    },
                ],
            },
        ],
    },
    {
        "category": {
            "name": "Human Resources",
            "slug": "human-resources",
            "summary": "Understand people-ops strategy, compliance rigor, and change enablement.",
            "icon": "briefcase",
        },
        "assessments": [
            {
                "title": "HR Compliance Pulse",
                "slug": "hr-compliance-pulse",
                "summary": "Checks knowledge of regional regulations and escalation playbooks.",
                "level": "advanced",
                "duration_minutes": 25,
                "skills_focus": ["Employment Law", "Policy Design", "Risk"],
                "scoring_rubric": {"weights": {"law": 0.4, "policy": 0.35, "risk": 0.25}},
                "questions": [
                    {
                        "order": 1,
                        "prompt": "When rolling out a global leave policy, which step ensures enforceability?",
                        "question_type": "single",
                        "choices": [
                            {"label": "Provide FAQ in Slack", "weight": 0.2},
                            {"label": "Audit labor codes per region", "weight": 1.0},
                            {"label": "Conduct manager office hours", "weight": 0.5},
                        ],
                    },
                    {
                        "order": 2,
                        "prompt": "Which signals indicate it is time to refresh an employee handbook?",
                        "question_type": "multi",
                        "choices": [
                            {"label": "Recent acquisition", "weight": 0.6},
                            {"label": "Regulatory change", "weight": 0.6},
                            {"label": "High NPS", "weight": 0.2},
                        ],
                    },
                    {
                        "order": 3,
                        "prompt": "Outline how you would partner with legal on a sensitive investigation.",
                        "question_type": "text",
                    },
                ],
            },
        ],
    },
    {
        "category": {
            "name": "General Behaviors",
            "slug": "general-behaviors",
            "summary": "Measure collaboration habits, decision making, and adaptability.",
            "icon": "users",
        },
        "assessments": [
            {
                "title": "Collaboration DNA",
                "slug": "collaboration-dna",
                "summary": "Highlights communication preferences and conflict navigation.",
                "level": "intro",
                "duration_minutes": 15,
                "skills_focus": ["Communication", "Conflict", "Ownership"],
                "scoring_rubric": {"dimensions": ["Clarity", "Empathy", "Bias for Action"]},
                "questions": [
                    {
                        "order": 1,
                        "prompt": "How do you keep distributed teammates aligned on objectives?",
                        "question_type": "text",
                    },
                    {
                        "order": 2,
                        "prompt": "Choose the behaviors that best describe your response to urgent blockers.",
                        "question_type": "multi",
                        "choices": [
                            {"label": "Mobilize available partners quickly", "weight": 0.6},
                            {"label": "Document workaround and share", "weight": 0.6},
                            {"label": "Pause other priorities indefinitely", "weight": 0.1},
                        ],
                    },
                    {
                        "order": 3,
                        "prompt": "Rate your comfort facilitating feedback conversations.",
                        "question_type": "scale",
                        "metadata": {"scale_labels": ["Still learning", "Confident", "Expert"]},
                    },
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with default assessment categories, assessments, and questions."

    @transaction.atomic
    def handle(self, *args, **options):
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
