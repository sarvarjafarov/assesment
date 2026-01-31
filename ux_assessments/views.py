import json

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import UXDesignAssessmentSession, UXDesignQuestion
from .services import evaluate_session, generate_question_set


class ApiKeyRequiredMixin:
    """Simple header-based API key authentication."""

    def dispatch(self, request, *args, **kwargs):
        api_key = getattr(settings, "API_ACCESS_TOKEN", None)
        if api_key:
            provided = request.headers.get("X-API-Key") or request.GET.get("api_key")
            if provided != api_key:
                return JsonResponse({"detail": "Invalid or missing API key"}, status=401)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class StartAssessmentView(ApiKeyRequiredMixin, View):
    def post(self, request):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
        candidate_id = payload.get("candidate_id")
        if not candidate_id:
            return JsonResponse({"detail": "candidate_id required"}, status=400)
        session, _ = UXDesignAssessmentSession.objects.get_or_create(
            candidate_id=candidate_id, defaults={"status": "draft"}
        )
        session.question_set = generate_question_set()
        session.status = "in_progress"
        session.save(update_fields=["question_set", "status"])
        return JsonResponse({"session_uuid": str(session.uuid)}, status=201)


class QuestionListView(ApiKeyRequiredMixin, View):
    def get(self, request, candidate_id):
        session = UXDesignAssessmentSession.objects.get(candidate_id=candidate_id)
        qs = UXDesignQuestion.objects.filter(id__in=session.question_set)
        questions = [
            {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "difficulty_level": q.difficulty_level,
                "category": q.category,
                "options": q.options,
                "scoring_weight": float(q.scoring_weight),
            }
            for q in qs
        ]
        return JsonResponse({"session_uuid": str(session.uuid), "questions": questions})


@method_decorator(csrf_exempt, name="dispatch")
class SubmitAssessmentView(ApiKeyRequiredMixin, View):
    def post(self, request, candidate_id):
        session = UXDesignAssessmentSession.objects.get(candidate_id=candidate_id)
        try:
            responses = json.loads(request.body or "[]")
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
        if not isinstance(responses, list):
            return JsonResponse({"detail": "Responses must be a list"}, status=400)
        session.responses = responses
        session.save(update_fields=["responses"])
        evaluate_session(session)
        return JsonResponse(
            {"detail": "Assessment submitted", "session_uuid": str(session.uuid)}
        )


class AssessmentResultView(ApiKeyRequiredMixin, View):
    def get(self, request, candidate_id):
        session = UXDesignAssessmentSession.objects.get(
            candidate_id=candidate_id, status="submitted"
        )
        payload = {
            "candidate_id": session.candidate_id,
            "hard_skill_score": session.hard_skill_score,
            "soft_skill_score": session.soft_skill_score,
            "overall_score": session.overall_score,
            "category_breakdown": session.category_breakdown,
            "recommendations": session.recommendations,
        }
        return JsonResponse(payload)
