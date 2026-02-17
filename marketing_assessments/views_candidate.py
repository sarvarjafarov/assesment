from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from candidate.constants import DEFAULT_HELP_TOPICS
from candidate.forms import CandidateFeedbackForm
from candidate.utils import send_switch_device_email, update_session_telemetry

from .forms import MarketingQuestionForm
from .models import DigitalMarketingAssessmentSession, DigitalMarketingQuestion
from .services import evaluate_session

MARKETING_GUIDANCE = {
    "multiple_choice": {
        "title": "Multiple choice",
        "body": "Pick the best option backed by metrics or logic. We only record one selection.",
    },
    "scenario": {
        "title": "Scenario response",
        "body": "Use the available data points and select the tactic you would try first.",
    },
    "ranking": {
        "title": "Rank the items",
        "body": "Reorder every item so it reflects your recommended priority. List them comma separated.",
    },
    "behavioral_most": {
        "title": "Behavioral block",
        "body": "Choose the statement that feels most like you for this situation. Only one per prompt.",
    },
    "behavioral_least": {
        "title": "Behavioral block",
        "body": "Choose the statement that is least like you. Avoid repeating previous picks.",
    },
    "reasoning": {
        "title": "Open response",
        "body": "Explain your thinking in 3–5 sentences, calling out assumptions and tradeoffs.",
    },
}

NON_LONGFORM_MARKETING_TYPES = {
    "multiple_choice",
    "scenario",
    "ranking",
    "behavioral_most",
    "behavioral_least",
}
MARKETING_PREVIEW_MIN = 150

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
        is_first_start = not self.session.started_at
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
            # Send new candidate notification on first start
            if is_first_start and self.session.client:
                from clients.services import send_new_candidate_alert, trigger_session_webhook, create_notification
                send_new_candidate_alert(self.session.client, self.session, "marketing")
                create_notification(
                    self.session.client,
                    "candidate_started",
                    "New Candidate Started",
                    message=f"{self.session.candidate_id} started the Marketing Assessment",
                    link_url=reverse('clients:assessment-manage', kwargs={'assessment_type': 'marketing'}),
                )
                trigger_session_webhook(self.session, "session.started")
        update_session_telemetry(self.session, request=request)
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
        # Count only responses whose question_id is in the current question_set
        valid_qids = set(self.session.question_set)
        valid_responses = [
            r for r in self.session.responses
            if r.get("question_id") in valid_qids
        ]
        # Prune stale responses from a previous question set
        if len(valid_responses) != len(self.session.responses):
            self.session.responses = valid_responses
            self.session.save(update_fields=["responses"])
        self.current_index = len(valid_responses)
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
                "guidance_tip": MARKETING_GUIDANCE.get(
                    self.current_question.question_type
                ),
                "show_preview": self.current_question.question_type
                not in NON_LONGFORM_MARKETING_TYPES,
                "preview_min_length": MARKETING_PREVIEW_MIN,
                "switch_device_url": reverse(
                    "candidate:marketing-send-link", args=[self.session.uuid]
                ),
                "help_topics": DEFAULT_HELP_TOPICS,
                "practice_url": reverse(
                    "candidate:session-practice", args=[self.session.uuid]
                ),
            }
        )

        context['show_onboarding'] = self.current_index == 0

        # Add deadline information
        deadline_info = self._calculate_deadline()
        if deadline_info:
            context['deadline_at'] = deadline_info['deadline_at']
            context['deadline_passed'] = deadline_info['deadline_passed']
            context['deadline_warning'] = deadline_info['deadline_warning']

        return context

    def _calculate_deadline(self):
        """Calculate deadline information for this session"""
        if self.session.deadline_type == 'absolute' and self.session.deadline_at:
            deadline_at = self.session.deadline_at
            now = timezone.now()
            deadline_passed = now > deadline_at
            # Warning if less than 24 hours remaining
            deadline_warning = not deadline_passed and (deadline_at - now).total_seconds() < 86400
            return {
                'deadline_at': deadline_at,
                'deadline_passed': deadline_passed,
                'deadline_warning': deadline_warning,
            }
        elif self.session.deadline_type == 'relative' and self.session.deadline_days:
            from datetime import timedelta
            # Calculate from scheduled_for or created_at
            base_time = self.session.scheduled_for or self.session.created_at
            deadline_at = base_time + timedelta(days=self.session.deadline_days)
            now = timezone.now()
            deadline_passed = now > deadline_at
            deadline_warning = not deadline_passed and (deadline_at - now).total_seconds() < 86400
            return {
                'deadline_at': deadline_at,
                'deadline_passed': deadline_passed,
                'deadline_warning': deadline_warning,
            }
        return None

    def form_valid(self, form):
        # Check if deadline has passed
        deadline_info = self._calculate_deadline()
        if deadline_info and deadline_info['deadline_passed']:
            from django.contrib import messages
            messages.error(
                self.request,
                f"The deadline for this assessment was {deadline_info['deadline_at'].strftime('%B %d, %Y at %I:%M %p')}. "
                "You can no longer submit responses."
            )
            return redirect("candidate:marketing-session", session_uuid=self.session.uuid)

        responses = list(self.session.responses)
        responses.append(form.to_response())
        self.session.responses = responses
        self.session.last_activity_at = timezone.now()
        self.session.save(update_fields=["responses", "last_activity_at"])
        update_session_telemetry(
            self.session, payload=self.request.POST.get("telemetry_payload")
        )
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
        if self.session.candidate_feedback_email:
            initial["contact_email"] = self.session.candidate_feedback_email
        if self.session.candidate_feedback_phone:
            initial["contact_phone"] = self.session.candidate_feedback_phone
        if self.session.candidate_feedback_opt_in:
            initial["allow_follow_up"] = True
        return initial

    def form_valid(self, form):
        self.session.candidate_feedback_score = int(form.cleaned_data["score"])
        self.session.candidate_feedback_comment = form.cleaned_data["comment"]
        self.session.candidate_feedback_email = form.cleaned_data.get("contact_email", "")
        self.session.candidate_feedback_phone = form.cleaned_data.get("contact_phone", "")
        self.session.candidate_feedback_opt_in = form.cleaned_data.get("allow_follow_up") or False
        self.session.candidate_feedback_submitted_at = timezone.now()
        self.session.save(
            update_fields=[
                "candidate_feedback_score",
                "candidate_feedback_comment",
                "candidate_feedback_email",
                "candidate_feedback_phone",
                "candidate_feedback_opt_in",
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


class MarketingSessionSendLinkView(View):
    """Email a session link so the candidate can resume on another device."""

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(
            DigitalMarketingAssessmentSession, uuid=kwargs["session_uuid"]
        )
        target_email = (request.POST.get("email") or "").strip()
        try:
            validate_email(target_email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("candidate:marketing-session", session_uuid=session.uuid)

        resume_link = request.build_absolute_uri(
            reverse("candidate:marketing-session", args=[session.uuid])
        )
        success, error = send_switch_device_email(
            email=target_email,
            candidate_name=session.candidate_id,
            resume_link=resume_link,
            assessment_label="Digital Marketing",
        )
        if success:
            messages.success(
                request,
                f"We emailed the secure link to {target_email}.",
            )
        else:
            messages.error(request, error or "We could not send the link right now.")
        return redirect("candidate:marketing-session", session_uuid=session.uuid)
