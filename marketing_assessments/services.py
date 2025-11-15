from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from random import shuffle
from statistics import mean

from django.utils import timezone

from .models import DigitalMarketingAssessmentSession, DigitalMarketingQuestion

CATEGORY_TARGETS = {
    "ppc": 5,
    "seo": 5,
    "analytics": 4,
    "content": 4,
    "social": 3,
    "strategy": 4,
    "behavioral": 3,
}

CATEGORY_WEIGHTS = {
    "ppc": Decimal("0.2"),
    "seo": Decimal("0.2"),
    "analytics": Decimal("0.15"),
    "content": Decimal("0.15"),
    "social": Decimal("0.1"),
    "strategy": Decimal("0.1"),
    "behavioral": Decimal("0.1"),
}

FIT_GROUPS = {
    "performance_marketing": ["ppc", "analytics", "strategy"],
    "seo": ["seo", "content"],
    "analytics": ["analytics", "strategy"],
    "content_marketing": ["content", "social", "strategy"],
    "generalist": ["ppc", "seo", "analytics", "content", "strategy"],
}

SENIORITY_RULES = [
    (Decimal("85"), "Lead"),
    (Decimal("75"), "Senior"),
    (Decimal("60"), "Mid"),
    (Decimal("45"), "Junior"),
    (Decimal("0"), "Needs development"),
]


def generate_question_set() -> list[int]:
    question_ids: list[int] = []
    for category, count in CATEGORY_TARGETS.items():
        qs = list(
            DigitalMarketingQuestion.objects.published()
            .filter(category=category)
            .order_by("?")[: count * 2]
        )
        question_ids.extend(q.id for q in qs[:count])
    shuffle(question_ids)
    return question_ids[:30]


def evaluate_session(session: DigitalMarketingAssessmentSession):
    question_map = {
        q.id: q
        for q in DigitalMarketingQuestion.objects.filter(id__in=session.question_set)
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
    return session
