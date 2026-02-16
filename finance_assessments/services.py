from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from random import shuffle
from statistics import mean

from django.utils import timezone

from .models import FinanceAssessmentSession, FinanceQuestion

CATEGORY_TARGETS = {
    "financial_analysis": 6,
    "budgeting": 5,
    "risk_compliance": 5,
    "strategic_finance": 5,
    "accounting_ops": 4,
    "treasury": 5,
    "behavioral": 3,
}

CATEGORY_WEIGHTS = {
    "financial_analysis": Decimal("0.20"),
    "budgeting": Decimal("0.15"),
    "risk_compliance": Decimal("0.15"),
    "strategic_finance": Decimal("0.15"),
    "accounting_ops": Decimal("0.10"),
    "treasury": Decimal("0.15"),
    "behavioral": Decimal("0.10"),
}

FIT_GROUPS = {
    "finance_manager": ["financial_analysis", "budgeting", "strategic_finance", "treasury"],
    "financial_analyst": ["financial_analysis", "budgeting", "accounting_ops"],
    "controller": ["accounting_ops", "risk_compliance", "budgeting"],
    "treasury_analyst": ["treasury", "risk_compliance", "financial_analysis"],
    "strategic_finance_lead": ["strategic_finance", "financial_analysis", "treasury"],
}

SENIORITY_RULES = [
    (Decimal("85"), "Lead"),
    (Decimal("75"), "Senior"),
    (Decimal("60"), "Mid"),
    (Decimal("45"), "Junior"),
    (Decimal("0"), "Needs development"),
]

LEVEL_DIFFICULTY_RANGES = {
    "junior": (1, 2),
    "mid": (2, 4),
    "senior": (3, 5),
}

LEVEL_QUESTION_COUNTS = {
    "junior": 25,
    "mid": 35,
    "senior": 40,
}

LEVEL_CATEGORY_MULTIPLIERS = {
    "junior": 0.8,
    "mid": 1.0,
    "senior": 1.3,
}


def generate_question_set(level: str = "mid") -> list[int]:
    """Generate a randomized question set filtered by assessment level."""
    min_diff, max_diff = LEVEL_DIFFICULTY_RANGES.get(level, (2, 4))
    total_questions = LEVEL_QUESTION_COUNTS.get(level, 35)
    multiplier = LEVEL_CATEGORY_MULTIPLIERS.get(level, 1.0)

    question_ids: list[int] = []

    for category, base_count in CATEGORY_TARGETS.items():
        count = max(2, int(base_count * multiplier))
        pool_size = count * 3

        qs = list(
            FinanceQuestion.objects.published()
            .filter(
                category=category,
                difficulty_level__gte=min_diff,
                difficulty_level__lte=max_diff,
            )
            .order_by("?")[:pool_size]
        )

        if len(qs) < count:
            qs = list(
                FinanceQuestion.objects.published()
                .filter(category=category)
                .order_by("?")[:pool_size]
            )

        shuffle(qs)
        question_ids.extend(q.id for q in qs[:count])

    shuffle(question_ids)
    return question_ids[:total_questions]


def evaluate_session(session: FinanceAssessmentSession):
    question_map = {
        q.id: q
        for q in FinanceQuestion.objects.filter(id__in=session.question_set)
    }
    cat_scores: dict[str, list[Decimal]] = defaultdict(list)
    behavioral_entries: list[int] = []
    for response in session.responses:
        question = question_map.get(response.get("question_id"))
        if not question:
            continue
        q_type = question.question_type
        if "behavioral" in q_type:
            marker = response.get("selected")
            behavioral_entries.append(1 if marker == "most" else -1)
            continue
        answer = response.get("answer")
        is_correct = answer == question.correct_answer
        score = Decimal(question.scoring_weight) if is_correct else Decimal("0")
        cat_scores[question.category].append(score)

    hard_scores = {
        category: (
            float(sum(scores) / (len(scores) or 1) * Decimal("100"))
            if scores
            else 0.0
        )
        for category, scores in cat_scores.items()
        if category != "behavioral"
    }
    hard_skill = sum(
        Decimal(str(hard_scores.get(cat, 0))) * CATEGORY_WEIGHTS.get(cat, Decimal("0"))
        for cat in hard_scores
    )
    hard_skill = round(float(hard_skill), 2)
    if behavioral_entries:
        soft_skill = round(((sum(behavioral_entries) / len(behavioral_entries)) + 1) * 50, 2)
    else:
        soft_skill = 50.0
    overall = round(0.7 * hard_skill + 0.3 * soft_skill, 2)

    fit_scores = {
        domain: round(
            mean([hard_scores.get(cat, 0) for cat in cats]) if cats else 0.0, 2
        )
        for domain, cats in FIT_GROUPS.items()
    }
    strengths = sorted(hard_scores, key=hard_scores.get, reverse=True)[:2]
    improvements = sorted(hard_scores, key=hard_scores.get)[:2]
    seniority = next(level for threshold, level in SENIORITY_RULES if Decimal(str(overall)) >= threshold)

    session.hard_skill_score = hard_skill
    session.soft_skill_score = soft_skill
    session.overall_score = overall
    session.category_breakdown = hard_scores
    session.recommendations = {
        "fit_scores": fit_scores,
        "strengths": strengths,
        "development": improvements,
        "seniority": seniority,
    }
    session.status = "submitted"
    session.submitted_at = timezone.now()
    session.save(
        update_fields=[
            "hard_skill_score",
            "soft_skill_score",
            "overall_score",
            "category_breakdown",
            "recommendations",
            "status",
            "submitted_at",
        ]
    )

    if session.client:
        from django.urls import reverse
        from clients.services import create_notification, send_completion_alert, trigger_session_webhook
        send_completion_alert(session.client, session, "finance")
        link_url = reverse('clients:assessment-detail', kwargs={'assessment_type': 'finance', 'session_uuid': session.uuid})
        create_notification(
            session.client,
            "assessment_completed",
            "Finance Assessment Completed",
            message=f"{session.candidate_id} completed the Finance Assessment",
            link_url=link_url,
        )
        trigger_session_webhook(session, "session.completed")

    return session
