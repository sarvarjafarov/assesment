from __future__ import annotations

from random import shuffle

from django.utils import timezone

from assessments.behavioral import build_behavioral_profile

from .models import BehavioralAssessmentSession, BehavioralQuestion


DEFAULT_QUESTION_COUNT = 30


def generate_question_set(count: int = DEFAULT_QUESTION_COUNT) -> list[int]:
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

    traits = report.get("traits", {})
    normalized = traits.get("normalized_scores", {}) if traits else {}
    eligibility = report.get("eligibility", {})
    risk_signals = report.get("risk_signals", {})

    session.trait_scores = normalized
    weighted_score = eligibility.get("weighted_score")
    session.eligibility_score = round(float(weighted_score), 2) if weighted_score is not None else None
    session.eligibility_label = eligibility.get("decision", "")
    session.profile_report = report
    session.risk_flags = risk_signals.get("flags", [])
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
