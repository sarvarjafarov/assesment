from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Iterable, Sequence

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .behavioral import build_behavioral_profile, parse_behavioral_value
from .models import (
    Assessment,
    AssessmentSession,
    CandidateProfile,
    Choice,
    CompanyProfile,
    PositionTask,
    Question,
    Response,
)

logger = logging.getLogger(__name__)
PASSING_SCORE = getattr(settings, "ASSESSMENT_PASSING_SCORE", 70.0)


@dataclass
class SessionInvite:
    candidate: CandidateProfile
    session: AssessmentSession
    assessment: Assessment
    created: bool


@dataclass
class SessionEvaluation:
    score: float
    breakdown: dict


@dataclass
class EmailDeliveryResult:
    sent: bool
    reason: str | None = None


def invite_candidate(
    *,
    assessment: Assessment,
    first_name: str,
    last_name: str = "",
    email: str,
    headline: str = "",
    metadata: dict | None = None,
    invited_by: str = "API",
    company: CompanyProfile | None = None,
    position_task: PositionTask | None = None,
    behavioral_focus: list[str] | None = None,
) -> SessionInvite:
    """Create a candidate profile and an associated assessment session."""

    candidate, _ = CandidateProfile.objects.update_or_create(
        email=email.lower(),
        defaults={
            "first_name": first_name.strip() or "Candidate",
            "last_name": last_name.strip(),
            "headline": headline,
            "metadata": metadata or {},
        },
    )

    if position_task and not company:
        company = position_task.company

    focus_values = list(behavioral_focus or [])
    if position_task and not focus_values:
        focus_values = list(position_task.behavioral_focus or [])

    session, created = AssessmentSession.objects.get_or_create(
        candidate=candidate,
        assessment=assessment,
        defaults={
            "status": "invited",
            "invited_by": invited_by,
            "invited_at": timezone.now(),
            "company": company,
            "position_task": position_task,
            "behavioral_focus": focus_values,
        },
    )
    if not created:
        session.status = "invited"
        session.invited_by = invited_by
        session.invited_at = timezone.now()
        session.company = company
        session.position_task = position_task
        session.behavioral_focus = focus_values
        session.save(
            update_fields=[
                "status",
                "invited_by",
                "invited_at",
                "company",
                "position_task",
                "behavioral_focus",
                "updated_at",
            ]
        )

    return SessionInvite(
        candidate=candidate, session=session, assessment=assessment, created=created
    )


def send_invite_email(
    *,
    candidate: CandidateProfile,
    assessment: Assessment,
    session: AssessmentSession,
    intro_link: str,
    start_link: str,
    invited_by: str,
    due_at=None,
    notes: str = "",
):
    """Send an email invitation with the candidate's unique session link."""

    context = {
        "candidate": candidate,
        "assessment": assessment,
        "session": session,
        "session_link": intro_link,
        "start_link": start_link,
        "invited_by": invited_by or "The Evalon Team",
        "due_at": due_at or session.due_at,
        "notes": notes or session.notes,
    }
    subject = f"{assessment.title} assessment invitation"
    text_body = render_to_string("emails/invite_candidate.txt", context)
    html_body = render_to_string("emails/invite_candidate.html", context)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    recipients = [candidate.email]
    if not settings.EMAIL_ENABLED:
        reason = "EMAIL_ENABLED is False; configure SMTP or set EMAIL_BACKEND."
        logger.info(
            reason + " Session %s invite link available at %s",
            session.pk,
            intro_link,
        )
        return EmailDeliveryResult(sent=False, reason=reason)
    try:
        send_mail(
            subject,
            text_body,
            from_email,
            recipients,
            html_message=html_body,
        )
        logger.info(
            "Invite email dispatched to %s for assessment %s",
            candidate.email,
            assessment.title,
        )
        return EmailDeliveryResult(sent=True)
    except Exception as exc:  # pragma: no cover - avoid failing invite on email issues
        logger.warning(
            "Failed to send invite email for session %s: %s", session.pk, exc
        )
        return EmailDeliveryResult(sent=False, reason=str(exc))


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
    behavioral_selections: list[dict] = []

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
        if question.question_type == Question.TYPE_BEHAVIORAL:
            behavioral_payload = answer.get("behavioral_responses") or []
            response.selected_choices.clear()
            response.answer_text = json.dumps(behavioral_payload)
            metadata = response.metadata or {}
            metadata["behavioral_partial"] = behavioral_payload
            response.metadata = metadata
            response.save(update_fields=["answer_text", "metadata", "updated_at"])
            behavioral_selections.extend(behavioral_payload)
            continue
        if question.question_type in {Question.TYPE_SINGLE, Question.TYPE_MULTI}:
            choice_ids = answer.get("choice_ids") or []
            valid_choices = list(
                Choice.objects.filter(question=question, id__in=choice_ids)
            )
            response.save()
            response.selected_choices.set(valid_choices)
            for choice in valid_choices:
                payload = parse_behavioral_value(choice.value)
                if payload:
                    behavioral_selections.append(payload)
        else:
            response.selected_choices.clear()
            response.save()

        if "score" in answer:
            response.score = answer["score"]
            response.save(update_fields=["answer_text", "score", "updated_at"])
        else:
            response.save(update_fields=["answer_text", "updated_at"])

    weight_profile = _resolve_behavioral_weight_profile(session.assessment)
    focus_traits = session.behavioral_focus_traits
    behavioral_profile = build_behavioral_profile(
        behavioral_selections,
        weight_profile=weight_profile,
        focus_traits=focus_traits,
    )

    now = timezone.now()
    session.last_activity_at = now

    if mark_completed:
        session.status = "completed"
        session.submitted_at = now
        evaluation: SessionEvaluation | None = None
        if overall_score is None or score_breakdown is None:
            evaluation = evaluate_session_performance(session)
        if overall_score is not None:
            session.overall_score = overall_score
        elif evaluation:
            session.overall_score = evaluation.score
        breakdown_payload = None
        if score_breakdown is not None:
            breakdown_payload = dict(score_breakdown)
        elif evaluation and evaluation.breakdown:
            breakdown_payload = dict(evaluation.breakdown)
        if behavioral_profile:
            breakdown_payload = breakdown_payload or {}
            breakdown_payload["behavioral_profile"] = behavioral_profile
        if focus_traits:
            breakdown_payload = breakdown_payload or {}
            breakdown_payload["behavioral_focus"] = focus_traits
        if breakdown_payload is not None:
            session.score_breakdown = breakdown_payload
        auto_decision_value = None
        if session.overall_score is not None and session.decision == "undecided":
            session.decision = determine_decision(session.overall_score)
            auto_decision_value = session.decision
        if auto_decision_value:
            breakdown = session.score_breakdown or {}
            breakdown.setdefault("auto_decision", auto_decision_value)
            session.score_breakdown = breakdown
        session.save(
            update_fields=[
                "status",
                "submitted_at",
                "overall_score",
                "score_breakdown",
                "decision",
                "last_activity_at",
                "updated_at",
            ]
        )

    else:
        session.save(update_fields=["last_activity_at", "updated_at"])

    return session


def evaluate_session_performance(
    session: AssessmentSession,
) -> SessionEvaluation | None:
    responses = (
        session.responses.select_related("question")
        .prefetch_related("selected_choices", "question__choices")
        .all()
    )
    question_scores: list[float] = []
    breakdown_entries: list[dict] = []
    for response in responses:
        question = response.question
        if question.question_type not in {Question.TYPE_SINGLE, Question.TYPE_MULTI}:
            continue
        max_weight = _question_max_weight(question)
        if not max_weight:
            continue
        selected_weight = sum(
            float(choice.weight) for choice in response.selected_choices.all()
        )
        ratio = max(0.0, min(selected_weight / max_weight, 1.0))
        question_scores.append(ratio)
        breakdown_entries.append(
            {
                "question_id": question.id,
                "prompt": question.prompt,
                "score": round(ratio * 100, 2),
            }
        )
    if not question_scores:
        return None
    overall = round(sum(question_scores) / len(question_scores) * 100, 2)
    return SessionEvaluation(
        score=overall, breakdown={"question_scores": breakdown_entries}
    )


def _question_max_weight(question: Question) -> float | None:
    choices = list(question.choices.all())
    if not choices:
        return None
    weights = [float(choice.weight) for choice in choices]
    if question.question_type == Question.TYPE_SINGLE:
        return max(weights)
    positive_weights = [weight for weight in weights if weight > 0]
    if not positive_weights:
        return None
    return sum(positive_weights)


def determine_decision(score: float) -> str:
    return "advance" if score >= PASSING_SCORE else "reject"


def _resolve_behavioral_weight_profile(assessment: Assessment | None) -> str | None:
    if not assessment or not assessment.scoring_rubric:
        return None
    rubric = assessment.scoring_rubric or {}
    profile = (
        rubric.get("behavioral_weight_profile")
        or rubric.get("behavioral_profile")
        or rubric.get("weight_profile")
    )
    if not profile:
        return None
    return str(profile).lower()
