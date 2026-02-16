from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from random import shuffle
from statistics import mean

from django.utils import timezone

from .models import ProductAssessmentSession, ProductQuestion

CATEGORY_TARGETS = {
    ProductQuestion.CATEGORY_PRODUCT: 5,
    ProductQuestion.CATEGORY_EXECUTION: 5,
    ProductQuestion.CATEGORY_STRATEGY: 5,
    ProductQuestion.CATEGORY_ANALYTICS: 4,
    ProductQuestion.CATEGORY_TECHNICAL: 4,
    ProductQuestion.CATEGORY_DESIGN: 3,
    ProductQuestion.CATEGORY_BEHAVIORAL: 4,
}

CATEGORY_WEIGHTS = {
    ProductQuestion.CATEGORY_PRODUCT: Decimal("0.2"),
    ProductQuestion.CATEGORY_EXECUTION: Decimal("0.2"),
    ProductQuestion.CATEGORY_STRATEGY: Decimal("0.15"),
    ProductQuestion.CATEGORY_ANALYTICS: Decimal("0.15"),
    ProductQuestion.CATEGORY_TECHNICAL: Decimal("0.1"),
    ProductQuestion.CATEGORY_DESIGN: Decimal("0.1"),
    ProductQuestion.CATEGORY_BEHAVIORAL: Decimal("0.1"),
}

FIT_GROUPS = {
    "product_strategy": [
        ProductQuestion.CATEGORY_PRODUCT,
        ProductQuestion.CATEGORY_STRATEGY,
    ],
    "execution": [
        ProductQuestion.CATEGORY_EXECUTION,
        ProductQuestion.CATEGORY_TECHNICAL,
    ],
    "insight": [
        ProductQuestion.CATEGORY_ANALYTICS,
        ProductQuestion.CATEGORY_DESIGN,
    ],
    "generalist": [
        ProductQuestion.CATEGORY_PRODUCT,
        ProductQuestion.CATEGORY_EXECUTION,
        ProductQuestion.CATEGORY_STRATEGY,
        ProductQuestion.CATEGORY_ANALYTICS,
        ProductQuestion.CATEGORY_TECHNICAL,
        ProductQuestion.CATEGORY_DESIGN,
    ],
}

SENIORITY_RULES = [
    (Decimal("85"), "Lead"),
    (Decimal("75"), "Senior"),
    (Decimal("60"), "Mid"),
    (Decimal("45"), "Junior"),
    (Decimal("0"), "Needs development"),
]

# Maps assessment level to question difficulty range (min, max) and total question count
LEVEL_DIFFICULTY_RANGES = {
    "junior": (1, 2),
    "mid": (2, 4),
    "senior": (3, 5),
}

# Total questions per assessment level (more questions = harder to cheat)
LEVEL_QUESTION_COUNTS = {
    "junior": 25,
    "mid": 35,
    "senior": 40,
}

# Category distribution multipliers per level
# Junior: fewer questions per category, Senior: more questions per category
LEVEL_CATEGORY_MULTIPLIERS = {
    "junior": 0.8,
    "mid": 1.0,
    "senior": 1.3,
}


def generate_question_set(level: str = "mid") -> list[int]:
    """Generate a randomized question set filtered by assessment level.

    Each level gets different difficulty questions and different total counts:
    - Junior (0-2 years): 25 questions, difficulty 1-2 (foundational)
    - Mid (2-5 years): 35 questions, difficulty 2-4 (applied knowledge)
    - Senior (5+ years): 40 questions, difficulty 3-5 (strategic thinking)

    Questions are randomly selected from a larger pool to prevent cheating.

    Args:
        level: Assessment level ('junior', 'mid', or 'senior')

    Returns:
        List of question IDs filtered by difficulty for the given level
    """
    min_diff, max_diff = LEVEL_DIFFICULTY_RANGES.get(level, (2, 4))
    total_questions = LEVEL_QUESTION_COUNTS.get(level, 35)
    multiplier = LEVEL_CATEGORY_MULTIPLIERS.get(level, 1.0)

    question_ids: list[int] = []

    for category, base_count in CATEGORY_TARGETS.items():
        # Adjust count based on level multiplier
        count = max(2, int(base_count * multiplier))

        # Pull from a larger pool (3x) to ensure randomization
        pool_size = count * 3

        # First try to get questions at the target difficulty level
        qs = list(
            ProductQuestion.objects.published()
            .filter(
                category=category,
                difficulty_level__gte=min_diff,
                difficulty_level__lte=max_diff,
            )
            .order_by("?")[:pool_size]
        )

        # Fallback: if not enough questions at level, expand to all difficulties
        if len(qs) < count:
            qs = list(
                ProductQuestion.objects.published()
                .filter(category=category)
                .order_by("?")[:pool_size]
            )

        # Shuffle and take the required count
        shuffle(qs)
        question_ids.extend(q.id for q in qs[:count])

    # Final shuffle and limit to total question count
    shuffle(question_ids)
    return question_ids[:total_questions]


def evaluate_session(session: ProductAssessmentSession):
    question_map = {
        q.id: q for q in ProductQuestion.objects.filter(id__in=session.question_set)
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
    seniority = next(
        level for threshold, level in SENIORITY_RULES if Decimal(str(overall)) >= threshold
    )

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

    # Send completion notification to client
    if session.client:
        from django.urls import reverse
        from clients.services import create_notification, send_completion_alert, trigger_session_webhook
        send_completion_alert(session.client, session, "product")
        link_url = reverse('clients:assessment-detail', kwargs={'assessment_type': 'product', 'session_uuid': session.uuid})
        create_notification(
            session.client,
            "assessment_completed",
            "Product Management Assessment Completed",
            message=f"{session.candidate_id} completed the Product Management Assessment",
            link_url=link_url,
        )
        trigger_session_webhook(session, "session.completed")

    return session
