from __future__ import annotations

from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from .forms import ProductQuestionForm
from .models import ProductAssessmentSession, ProductQuestion
from .services import evaluate_session


class ProductAssessmentView(FormView):
    template_name = "candidate/pm_session.html"
    form_class = ProductQuestionForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            ProductAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if self.session.status == "submitted":
            return redirect("candidate:pm-complete", session_uuid=self.session.uuid)
        if not self.session.started_at:
            self.session.started_at = timezone.now()
            self.session.save(update_fields=["started_at"])
        deadline = self.session.started_at + timedelta(
            minutes=self.session.duration_minutes or 0
        )
        now = timezone.now()
        if self.session.duration_minutes and now > deadline:
            return redirect("candidate:pm-expired", session_uuid=self.session.uuid)
        self.remaining_minutes = max(0, int((deadline - now).total_seconds() // 60))
        self.current_index = len(self.session.responses)
        if self.current_index >= len(self.session.question_set):
            evaluate_session(self.session)
            return redirect("candidate:pm-complete", session_uuid=self.session.uuid)
        self.current_question = ProductQuestion.objects.get(
            id=self.session.question_set[self.current_index]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["question"] = self.current_question
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = len(self.session.question_set)
        context.update(
            {
                "session": self.session,
                "question": self.current_question,
                "step_number": self.current_index + 1,
                "total_steps": total,
                "progress_percent": int((self.current_index / total) * 100),
                "remaining_minutes": self.remaining_minutes,
            }
        )
        return context

    def form_valid(self, form):
        responses = list(self.session.responses)
        responses.append(form.to_response())
        self.session.responses = responses
        self.session.save(update_fields=["responses"])
        if len(responses) >= len(self.session.question_set):
            evaluate_session(self.session)
            return redirect("candidate:pm-complete", session_uuid=self.session.uuid)
        return redirect("candidate:pm-session", session_uuid=self.session.uuid)


class ProductAssessmentCompleteView(TemplateView):
    template_name = "candidate/pm_complete.html"

    def get_context_data(self, **kwargs):
        session = get_object_or_404(
            ProductAssessmentSession, uuid=kwargs["session_uuid"]
        )
        context = super().get_context_data(**kwargs)
        context["session"] = session
        if session.started_at and session.submitted_at:
            duration = (session.submitted_at - session.started_at).total_seconds() / 60
            context["elapsed_minutes"] = round(duration, 1)
        return context


class ProductAssessmentExpiredView(TemplateView):
    template_name = "candidate/pm_expired.html"

    def get_context_data(self, **kwargs):
        session = get_object_or_404(
            ProductAssessmentSession, uuid=kwargs["session_uuid"]
        )
        context = super().get_context_data(**kwargs)
        context["session"] = session
        return context
