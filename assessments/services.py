from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from django.utils import timezone

from .models import (
    Assessment,
    AssessmentSession,
    CandidateProfile,
    Choice,
    Question,
    Response,
)


@dataclass
class SessionInvite:
    candidate: CandidateProfile
    session: AssessmentSession
    created: bool


def invite_candidate(
    *,
    assessment: Assessment,
    first_name: str,
    last_name: str = "",
    email: str,
    headline: str = "",
    metadata: dict | None = None,
    invited_by: str = "API",
) -> SessionInvite:
    """Create or update a candidate + associated assessment session."""

    candidate, _ = CandidateProfile.objects.update_or_create(
        email=email.lower(),
        defaults={
            "first_name": first_name.strip() or "Candidate",
            "last_name": last_name.strip(),
            "headline": headline,
            "metadata": metadata or {},
        },
    )

    session, created = AssessmentSession.objects.get_or_create(
        candidate=candidate,
        assessment=assessment,
        defaults={"status": "invited"},
    )
    session.status = "invited"
    session.invited_by = invited_by
    session.invited_at = timezone.now()
    session.save(update_fields=["status", "invited_by", "invited_at", "updated_at"])

    return SessionInvite(candidate=candidate, session=session, created=created)


def record_responses(
    *,
    session: AssessmentSession,
    answers: Sequence[dict],
    overall_score: float | None = None,
    score_breakdown: dict | None = None,
    mark_completed: bool = True,
) -> AssessmentSession:
    """Persist candidate answers and optionally finalize the session."""

    question_map = {
        q.id: q
        for q in Question.objects.filter(
            assessment=session.assessment, id__in=[a["question_id"] for a in answers]
        )
    }

    for answer in answers:
        question = question_map.get(answer["question_id"])
        if not question:
            continue

        response, _ = Response.objects.get_or_create(
            session=session,
            question=question,
            defaults={"answer_text": ""},
        )
        response.answer_text = answer.get("answer_text", "")
        if question.question_type in {Question.TYPE_SINGLE, Question.TYPE_MULTI}:
            choice_ids = answer.get("choice_ids") or []
            valid_choices = Choice.objects.filter(
                question=question, id__in=choice_ids
            )
            response.save()
            response.selected_choices.set(valid_choices)
        else:
            response.selected_choices.clear()
            response.save()

        if "score" in answer:
            response.score = answer["score"]
            response.save(update_fields=["answer_text", "score", "updated_at"])
        else:
            response.save(update_fields=["answer_text", "updated_at"])

    if mark_completed:
        session.status = "completed"
        session.submitted_at = timezone.now()
        if overall_score is not None:
            session.overall_score = overall_score
        if score_breakdown is not None:
            session.score_breakdown = score_breakdown
        session.save(
            update_fields=[
                "status",
                "submitted_at",
                "overall_score",
                "score_breakdown",
                "updated_at",
            ]
        )

    return session
