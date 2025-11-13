import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Assessment, AssessmentSession, RoleCategory
from .services import invite_candidate, record_responses, send_invite_email


class ApiKeyRequiredMixin:
    """Simple header-based API key authentication."""

    require_key = True

    def dispatch(self, request, *args, **kwargs):
        api_key = getattr(settings, "API_ACCESS_TOKEN", None)
        if self.require_key and api_key:
            provided = request.headers.get("X-API-Key") or request.GET.get("api_key")
            if provided != api_key:
                return JsonResponse({"detail": "Invalid or missing API key"}, status=401)
        return super().dispatch(request, *args, **kwargs)


class CategoryListView(View):
    """Return active categories with their currently available assessments."""

    def get(self, request):
        categories = (
            RoleCategory.objects.filter(is_active=True)
            .prefetch_related("assessments")
            .order_by("name")
        )
        payload = []
        for category in categories:
            payload.append(
                {
                    "name": category.name,
                    "slug": category.slug,
                    "summary": category.summary,
                    "assessments": [
                        {
                            "title": assessment.title,
                            "slug": assessment.slug,
                            "level": assessment.level,
                            "duration_minutes": assessment.duration_minutes,
                            "skills_focus": assessment.skills_focus,
                        }
                        for assessment in category.assessments.filter(is_active=True)
                    ],
                }
            )
        return JsonResponse({"categories": payload})


class AssessmentDetailView(View):
    """Provide detail for a single assessment including questions/choices."""

    def get(self, request, slug):
        assessment = get_object_or_404(
            Assessment.objects.prefetch_related("questions__choices"),
            slug=slug,
            is_active=True,
        )
        questions = []
        for question in assessment.questions.all():
            questions.append(
                {
                    "id": question.id,
                    "prompt": question.prompt,
                    "question_type": question.question_type,
                    "order": question.order,
                    "weight": float(question.weight),
                    "metadata": question.metadata,
                    "choices": [
                        {
                            "id": choice.id,
                            "label": choice.label,
                            "value": choice.value,
                            "weight": float(choice.weight),
                        }
                        for choice in question.choices.all()
                    ],
                }
            )
        data = {
            "title": assessment.title,
            "slug": assessment.slug,
            "summary": assessment.summary,
            "category": assessment.category.name,
            "level": assessment.level,
            "duration_minutes": assessment.duration_minutes,
            "skills_focus": assessment.skills_focus,
            "questions": questions,
        }
        return JsonResponse(data)


@method_decorator(csrf_exempt, name="dispatch")
class InvitationCreateApiView(ApiKeyRequiredMixin, View):
    """Create candidate + assessment session via API."""

    def post(self, request):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

        email = payload.get("email")
        full_name = payload.get("full_name") or ""
        if not email or not full_name:
            return JsonResponse(
                {"detail": "Both email and full_name are required."}, status=400
            )

        assessment = None
        if slug := payload.get("assessment_slug"):
            assessment = Assessment.objects.filter(slug=slug, is_active=True).first()
        elif category_slug := payload.get("category_slug"):
            category = RoleCategory.objects.filter(
                slug=category_slug, is_active=True
            ).first()
            if category:
                assessment = (
                    category.assessments.filter(is_active=True).order_by("title").first()
                )

        if not assessment:
            return JsonResponse(
                {"detail": "Assessment could not be resolved."}, status=404
            )

        first_name, last_name = _split_name(full_name)
        invite = invite_candidate(
            assessment=assessment,
            first_name=first_name,
            last_name=last_name,
            email=email,
            headline=payload.get("headline", ""),
            metadata=payload.get("metadata") or {},
            invited_by="API",
        )
        notes = payload.get("notes", "")
        due_at_input = payload.get("due_at")
        due_at = None
        if due_at_input:
            due_at = parse_datetime(due_at_input)
            if not due_at:
                return JsonResponse(
                    {"detail": "due_at must be an ISO datetime string."}, status=400
                )
            if timezone.is_naive(due_at):
                due_at = timezone.make_aware(due_at, timezone.get_current_timezone())

        session_updates = []
        if notes:
            invite.session.notes = notes
            session_updates.append("notes")
        if due_at:
            invite.session.due_at = due_at
            session_updates.append("due_at")
        if session_updates:
            session_updates.append("updated_at")
            invite.session.save(update_fields=session_updates)

        intro_link = request.build_absolute_uri(
            reverse("candidate:session-entry", args=[invite.session.uuid])
        )
        start_link = request.build_absolute_uri(
            reverse("candidate:session-start", args=[invite.session.uuid])
        )
        send_invite_email(
            candidate=invite.candidate,
            assessment=assessment,
            session=invite.session,
            intro_link=intro_link,
            start_link=start_link,
            invited_by="API",
            notes=notes,
            due_at=due_at,
        )
        response_data = {
            "session_uuid": str(invite.session.uuid),
            "assessment": assessment.slug,
            "candidate": {
                "id": invite.candidate.id,
                "first_name": invite.candidate.first_name,
                "last_name": invite.candidate.last_name,
                "email": invite.candidate.email,
            },
            "status": invite.session.status,
        }
        return JsonResponse(response_data, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class SessionResponseApiView(ApiKeyRequiredMixin, View):
    """Attach candidate responses to a session."""

    def post(self, request, session_uuid):
        session = get_object_or_404(AssessmentSession, uuid=session_uuid)
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

        answers = payload.get("responses") or []
        if not isinstance(answers, list):
            return JsonResponse({"detail": "responses must be a list."}, status=400)

        record_responses(
            session=session,
            answers=answers,
            overall_score=payload.get("overall_score"),
            score_breakdown=payload.get("score_breakdown"),
        )

        submitted = session.submitted_at.isoformat() if session.submitted_at else None
        return JsonResponse(
            {
                "session_uuid": str(session.uuid),
                "status": session.status,
                "submitted_at": submitted,
            }
        )


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(" ", 1)
    first = parts[0] if parts else "Candidate"
    last = parts[1] if len(parts) > 1 else ""
    return first, last
