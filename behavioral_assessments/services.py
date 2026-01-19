from __future__ import annotations

from random import shuffle

from django.utils import timezone

from assessments.behavioral import build_behavioral_profile

from .models import BehavioralAssessmentSession, BehavioralQuestion


DEFAULT_QUESTION_COUNT = 30

# Maps assessment level to question difficulty range (min, max)
LEVEL_DIFFICULTY_RANGES = {
    "junior": (1, 2),
    "mid": (2, 4),
    "senior": (3, 5),
}


def generate_question_set(count: int = DEFAULT_QUESTION_COUNT, level: str = "mid") -> list[int]:
    """Generate a question set filtered by assessment level.

    Args:
        count: Number of questions to include
        level: Assessment level ('junior', 'mid', or 'senior')

    Returns:
        List of question IDs filtered by difficulty for the given level
    """
    min_diff, max_diff = LEVEL_DIFFICULTY_RANGES.get(level, (2, 4))

    # First try to get questions at the target difficulty level
    ids = list(
        BehavioralQuestion.objects.published()
        .filter(
            difficulty_level__gte=min_diff,
            difficulty_level__lte=max_diff,
        )
        .values_list("id", flat=True)
    )

    # Fallback: if not enough questions at level, get all questions
    if len(ids) < count:
        ids = list(
            BehavioralQuestion.objects.published().values_list("id", flat=True)
        )

    if not ids:
        return []
    shuffle(ids)
    return ids[:count]


def evaluate_session(session: BehavioralAssessmentSession):
    selections: list[dict] = []
    for item in session.responses:
        most_like = item.get("most_like")
        least_like = item.get("least_like")
        if most_like:
            selections.append({
                "statement_id": most_like,
                "response_type": "most_like_me",
            })
        if least_like:
            selections.append({
                "statement_id": least_like,
                "response_type": "least_like_me",
            })
    report = build_behavioral_profile(selections)
    if not report:
        return session

    normalized = report.get("normalized_scores") or {}
    eligibility = report.get("eligibility") or {}
    red_flag_report = report.get("red_flag_report") or {}

    session.trait_scores = normalized
    weighted_score = eligibility.get("score")
    session.eligibility_score = (
        round(float(weighted_score), 2) if weighted_score is not None else None
    )
    session.eligibility_label = eligibility.get("decision", "")
    session.profile_report = report
    session.risk_flags = red_flag_report.get("red_flags") or report.get("red_flags") or []
    session.status = "submitted"
    session.submitted_at = timezone.now()
    session.save(
        update_fields=[
            "trait_scores",
            "eligibility_score",
            "eligibility_label",
            "profile_report",
            "risk_flags",
            "status",
            "submitted_at",
            "updated_at",
        ]
    )
    return session
