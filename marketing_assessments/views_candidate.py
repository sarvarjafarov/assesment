from __future__ import annotations

from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from candidate.forms import CandidateFeedbackForm

from .forms import MarketingQuestionForm
from .models import DigitalMarketingAssessmentSession, DigitalMarketingQuestion
from .services import evaluate_session


class MarketingAssessmentView(FormView):
    template_name = "candidate/marketing_session.html"
    form_class = MarketingQuestionForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            DigitalMarketingAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if self.session.status == "submitted":
            return redirect(
                "candidate:marketing-complete", session_uuid=self.session.uuid
            )
        if self.session.status == "paused":
            return redirect(
                "candidate:marketing-paused", session_uuid=self.session.uuid
            )
        updates: list[str] = []
        now = timezone.now()
        if not self.session.started_at:
            self.session.started_at = now
            updates.append("started_at")
        if self.session.status == "draft":
            self.session.status = "in_progress"
            updates.append("status")
        if not self.session.last_activity_at:
            self.session.last_activity_at = now
            updates.append("last_activity_at")
        if updates:
            self.session.save(update_fields=updates + ["updated_at"])
        duration_minutes = self.session.duration_minutes or 0
        if duration_minutes:
            pause_delta = timedelta(
                seconds=int(self.session.total_paused_seconds or 0)
            )
            deadline = self.session.started_at + timedelta(
                minutes=duration_minutes
            ) + pause_delta
            if now > deadline:
                return redirect(
                    "candidate:marketing-expired", session_uuid=self.session.uuid
                )
            self.remaining_minutes = max(
                0, int((deadline - now).total_seconds() // 60)
            )
        else:
            self.remaining_minutes = None
        self.current_index = len(self.session.responses)
        if self.current_index >= len(self.session.question_set):
            evaluate_session(self.session)
            return redirect(
                "candidate:marketing-complete", session_uuid=self.session.uuid
            )
        self.current_question = DigitalMarketingQuestion.objects.get(
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
                "pause_url": reverse(
                    "candidate:marketing-pause", args=[self.session.uuid]
                ),
                "last_saved_at": self.session.last_activity_at,
            }
        )
        return context

    def form_valid(self, form):
        responses = list(self.session.responses)
        responses.append(form.to_response())
        self.session.responses = responses
        self.session.last_activity_at = timezone.now()
        self.session.save(update_fields=["responses", "last_activity_at"])
        if len(responses) >= len(self.session.question_set):
            evaluate_session(self.session)
            return redirect(
                "candidate:marketing-complete", session_uuid=self.session.uuid
            )
        return redirect(
            "candidate:marketing-session", session_uuid=self.session.uuid
        )


class MarketingAssessmentCompleteView(FormView):
    template_name = "candidate/marketing_complete.html"
    form_class = CandidateFeedbackForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            DigitalMarketingAssessmentSession, uuid=kwargs["session_uuid"]
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
        return reverse("candidate:marketing-complete", args=[self.session.uuid])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        if self.session.started_at and self.session.submitted_at:
            duration = (self.session.submitted_at - self.session.started_at).total_seconds() / 60
            context["elapsed_minutes"] = round(duration, 1)
        context["feedback_submitted"] = bool(self.session.candidate_feedback_score)
        return context


class MarketingAssessmentExpiredView(TemplateView):
    template_name = "candidate/marketing_expired.html"

    def get_context_data(self, **kwargs):
        session = get_object_or_404(
            DigitalMarketingAssessmentSession, uuid=kwargs["session_uuid"]
        )
        context = super().get_context_data(**kwargs)
        context["session"] = session
        return context


class MarketingSessionPauseView(View):
    """Handles manual pause requests for the marketing assessment."""

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(
            DigitalMarketingAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if session.status != "submitted":
            now = timezone.now()
            session.status = "paused"
            session.paused_at = now
            session.last_activity_at = now
            session.save(
                update_fields=[
                    "status",
                    "paused_at",
                    "last_activity_at",
                    "updated_at",
                ]
            )
        return redirect("candidate:marketing-paused", session_uuid=session.uuid)


class MarketingSessionPausedView(TemplateView):
    template_name = "candidate/pause_state.html"

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            DigitalMarketingAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if self.session.status != "paused":
            return redirect(
                "candidate:marketing-session", session_uuid=self.session.uuid
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        context["assessment_label"] = "Digital Marketing Assessment"
        context["paused_at"] = self.session.paused_at
        context["resume_url"] = reverse(
            "candidate:marketing-resume", args=[self.session.uuid]
        )
        context["last_saved_at"] = self.session.last_activity_at
        return context


class MarketingSessionResumeView(View):
    """Resumes a paused marketing assessment session."""

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(
            DigitalMarketingAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if session.status != "paused":
            return redirect("candidate:marketing-session", session_uuid=session.uuid)
        now = timezone.now()
        paused_seconds = session.total_paused_seconds or 0
        if session.paused_at:
            paused_seconds += int((now - session.paused_at).total_seconds())
        session.total_paused_seconds = paused_seconds
        session.paused_at = None
        session.status = "in_progress"
        session.last_activity_at = now
        session.save(
            update_fields=[
                "status",
                "paused_at",
                "total_paused_seconds",
                "last_activity_at",
                "updated_at",
            ]
        )
        return redirect("candidate:marketing-session", session_uuid=session.uuid)
