from __future__ import annotations

from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from candidate.forms import CandidateFeedbackForm
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


class BehavioralAssessmentCompleteView(FormView):
    template_name = "candidate/behavioral_complete.html"
    form_class = CandidateFeedbackForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.session.candidate_feedback_score:
            initial["score"] = self.session.candidate_feedback_score
        if self.session.candidate_feedback_comment:
            initial["comment"] = self.session.candidate_feedback_comment
        return initial

    def form_valid(self, form):
        self.session.candidate_feedback_score = int(form.cleaned_data["score"])
        self.session.candidate_feedback_comment = form.cleaned_data["comment"]
        self.session.candidate_feedback_submitted_at = timezone.now()
        self.session.save(
            update_fields=[
                "candidate_feedback_score",
                "candidate_feedback_comment",
                "candidate_feedback_submitted_at",
            ]
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("candidate:behavioral-complete", args=[self.session.uuid])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        if self.session.started_at and self.session.submitted_at:
            duration = (self.session.submitted_at - self.session.started_at).total_seconds() / 60
            context["elapsed_minutes"] = round(duration, 1)
        context["trait_scores"] = self.session.trait_scores or {}
        context["eligibility"] = {
            "score": self.session.eligibility_score,
            "label": self.session.eligibility_label,
        }
        context["feedback_submitted"] = bool(self.session.candidate_feedback_score)
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
