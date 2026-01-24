"""
Candidate-facing views for custom assessments.
"""
from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from candidate.constants import DEFAULT_HELP_TOPICS
from candidate.forms import CandidateFeedbackForm

from .forms import CandidateAnswerForm
from .models import CustomAssessmentSession, CustomQuestion


class CustomAssessmentView(FormView):
    """Main view for candidates taking a custom assessment."""

    template_name = "custom_assessments/candidate_session.html"
    form_class = CandidateAnswerForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            CustomAssessmentSession, uuid=kwargs["session_uuid"]
        )

        # Redirect if already submitted
        if self.session.status == "submitted":
            return redirect(
                "candidate:custom-complete", session_uuid=self.session.uuid
            )

        # Initialize question order if needed
        if not self.session.question_order:
            questions = list(
                self.session.assessment.questions.values_list("pk", flat=True)
            )
            import random
            random.shuffle(questions)
            self.session.question_order = questions
            self.session.save(update_fields=["question_order", "updated_at"])

        # Start the session if it's a draft
        now = timezone.now()
        is_first_start = not self.session.started_at
        if not self.session.started_at:
            self.session.started_at = now
            self.session.status = "in_progress"
            self.session.save(update_fields=["started_at", "status", "updated_at"])

            # Send new candidate notification
            if is_first_start and self.session.client:
                from clients.services import send_new_candidate_alert
                send_new_candidate_alert(
                    self.session.client, self.session, "custom"
                )

        # Check deadline
        if self.session.deadline_at and now > self.session.deadline_at:
            return redirect(
                "candidate:custom-expired", session_uuid=self.session.uuid
            )

        # Calculate remaining time
        time_limit = self.session.assessment.time_limit_minutes
        if time_limit:
            deadline = self.session.started_at + timedelta(minutes=time_limit)
            if now > deadline:
                return redirect(
                    "candidate:custom-expired", session_uuid=self.session.uuid
                )
            self.remaining_minutes = max(
                0, int((deadline - now).total_seconds() // 60)
            )
        else:
            self.remaining_minutes = None

        # Get current question
        self.current_index = self.session.current_question_index
        if self.current_index >= len(self.session.question_order):
            self.session.submit()
            return redirect(
                "candidate:custom-complete", session_uuid=self.session.uuid
            )

        question_id = self.session.question_order[self.current_index]
        self.current_question = get_object_or_404(CustomQuestion, pk=question_id)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["question"] = self.current_question
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = len(self.session.question_order)

        context.update(
            {
                "session": self.session,
                "assessment": self.session.assessment,
                "question": self.current_question,
                "step_number": self.current_index + 1,
                "total_steps": total,
                "progress_percent": int((self.current_index / total) * 100),
                "remaining_minutes": self.remaining_minutes,
                "help_topics": DEFAULT_HELP_TOPICS,
            }
        )

        # Add deadline information
        if self.session.deadline_at:
            now = timezone.now()
            context["deadline_at"] = self.session.deadline_at
            context["deadline_passed"] = now > self.session.deadline_at
            context["deadline_warning"] = (
                not context["deadline_passed"]
                and (self.session.deadline_at - now).total_seconds() < 86400
            )

        return context

    def form_valid(self, form):
        # Check if deadline has passed
        if self.session.deadline_at and timezone.now() > self.session.deadline_at:
            messages.error(
                self.request,
                f"The deadline for this assessment was {self.session.deadline_at.strftime('%B %d, %Y at %I:%M %p')}. "
                "You can no longer submit responses."
            )
            return redirect(
                "candidate:custom-session", session_uuid=self.session.uuid
            )

        # Record the answer
        answer = form.cleaned_data["answer"]
        self.session.record_answer(self.current_question.pk, answer)

        # Move to next question
        self.session.current_question_index += 1
        self.session.save(update_fields=["current_question_index", "updated_at"])

        # Check if assessment is complete
        if self.session.current_question_index >= len(self.session.question_order):
            self.session.submit()
            return redirect(
                "candidate:custom-complete", session_uuid=self.session.uuid
            )

        return redirect(
            "candidate:custom-session", session_uuid=self.session.uuid
        )


class CustomAssessmentCompleteView(FormView):
    """Completion page for custom assessments with feedback form."""

    template_name = "custom_assessments/candidate_complete.html"
    form_class = CandidateFeedbackForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            CustomAssessmentSession, uuid=kwargs["session_uuid"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        context["assessment"] = self.session.assessment

        # Calculate elapsed time
        if self.session.started_at and self.session.completed_at:
            duration = (
                self.session.completed_at - self.session.started_at
            ).total_seconds() / 60
            context["elapsed_minutes"] = round(duration, 1)

        return context

    def get_success_url(self):
        return reverse("candidate:custom-complete", args=[self.session.uuid])


class CustomAssessmentExpiredView(TemplateView):
    """View shown when assessment time has expired."""

    template_name = "custom_assessments/candidate_expired.html"

    def get_context_data(self, **kwargs):
        session = get_object_or_404(
            CustomAssessmentSession, uuid=kwargs["session_uuid"]
        )
        context = super().get_context_data(**kwargs)
        context["session"] = session
        context["assessment"] = session.assessment
        return context
