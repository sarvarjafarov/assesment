from __future__ import annotations

from random import shuffle

from django.utils import timezone

from assessments.behavioral import build_behavioral_profile

from .models import BehavioralAssessmentSession, BehavioralQuestion


# Maps assessment level to question difficulty range (min, max)
LEVEL_DIFFICULTY_RANGES = {
    "junior": (1, 2),
    "mid": (2, 4),
    "senior": (3, 5),
}

# Total questions per assessment level (more questions = harder to cheat)
LEVEL_QUESTION_COUNTS = {
    "junior": 20,
    "mid": 30,
    "senior": 35,
}


def generate_question_set(level: str = "mid") -> list[int]:
    """Generate a randomized question set filtered by assessment level.

    Each level gets different difficulty questions and different total counts:
    - Junior (0-2 years): 20 questions, difficulty 1-2 (foundational)
    - Mid (2-5 years): 30 questions, difficulty 2-4 (applied)
    - Senior (5+ years): 35 questions, difficulty 3-5 (complex scenarios)

    Questions are randomly selected from a larger pool to prevent cheating.

    Args:
        level: Assessment level ('junior', 'mid', or 'senior')

    Returns:
        List of question IDs filtered by difficulty for the given level
    """
    min_diff, max_diff = LEVEL_DIFFICULTY_RANGES.get(level, (2, 4))
    total_questions = LEVEL_QUESTION_COUNTS.get(level, 30)

    # Pull from a larger pool (2x) to ensure randomization
    pool_size = total_questions * 2

    # First try to get questions at the target difficulty level
    ids = list(
        BehavioralQuestion.objects.published()
        .filter(
            difficulty_level__gte=min_diff,
            difficulty_level__lte=max_diff,
        )
        .order_by("?")[:pool_size]
    )

    # Fallback: if not enough questions at level, get all questions
    if len(ids) < total_questions:
        ids = list(
            BehavioralQuestion.objects.published()
            .order_by("?")[:pool_size]
        )

    if not ids:
        return []

    # Shuffle and take required count
    shuffle(ids)
    return ids[:total_questions]


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

    # Send completion notification to client
    if session.client:
        from clients.services import send_completion_alert, trigger_session_webhook
        send_completion_alert(session.client, session, "behavioral")
        trigger_session_webhook(session, "session.completed")

    return session
