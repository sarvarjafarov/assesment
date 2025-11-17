from __future__ import annotations

from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from .forms import BehavioralQuestionForm
from .models import BehavioralAssessmentSession, BehavioralQuestion
from .services import evaluate_session


class BehavioralAssessmentView(FormView):
    template_name = "candidate/behavioral_session.html"
    form_class = BehavioralQuestionForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if self.session.status == "submitted":
            return redirect("candidate:behavioral-complete", session_uuid=self.session.uuid)
        if not self.session.started_at:
            self.session.started_at = timezone.now()
            self.session.save(update_fields=["started_at"])
        deadline = self.session.started_at + timedelta(minutes=self.session.duration_minutes or 0)
        now = timezone.now()
        if self.session.duration_minutes and now > deadline:
            return redirect("candidate:behavioral-expired", session_uuid=self.session.uuid)
        self.remaining_minutes = max(0, int((deadline - now).total_seconds() // 60))
        self.current_index = len(self.session.responses)
        if self.current_index >= len(self.session.question_set):
            evaluate_session(self.session)
            return redirect("candidate:behavioral-complete", session_uuid=self.session.uuid)
        question_id = self.session.question_set[self.current_index]
        self.current_question = get_object_or_404(BehavioralQuestion, id=question_id)
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
            return redirect("candidate:behavioral-complete", session_uuid=self.session.uuid)
        return redirect("candidate:behavioral-session", session_uuid=self.session.uuid)


class BehavioralAssessmentCompleteView(TemplateView):
    template_name = "candidate/behavioral_complete.html"

    def get_context_data(self, **kwargs):
        session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
        )
        context = super().get_context_data(**kwargs)
        context["session"] = session
        if session.started_at and session.submitted_at:
            duration = (session.submitted_at - session.started_at).total_seconds() / 60
            context["elapsed_minutes"] = round(duration, 1)
        context["trait_scores"] = session.trait_scores or {}
        context["eligibility"] = {
            "score": session.eligibility_score,
            "label": session.eligibility_label,
        }
        return context


class BehavioralAssessmentExpiredView(TemplateView):
    template_name = "candidate/behavioral_expired.html"

    def get_context_data(self, **kwargs):
        session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
        )
        context = super().get_context_data(**kwargs)
        context["session"] = session
        return context
