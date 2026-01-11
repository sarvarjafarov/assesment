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
from .forms import BehavioralQuestionForm
from .models import BehavioralAssessmentSession, BehavioralQuestion
from .services import evaluate_session

BEHAVIORAL_GUIDANCE = {
    "title": "Behavioral block",
    "body": "Pick one statement for each column. Each statement can only be used once per block.",
}

class BehavioralAssessmentView(FormView):
    template_name = "candidate/behavioral_session.html"
    form_class = BehavioralQuestionForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if self.session.status == "submitted":
            return redirect("candidate:behavioral-complete", session_uuid=self.session.uuid)
        if self.session.status == "paused":
            return redirect("candidate:behavioral-paused", session_uuid=self.session.uuid)
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
                    "candidate:behavioral-expired", session_uuid=self.session.uuid
                )
            self.remaining_minutes = max(
                0, int((deadline - now).total_seconds() // 60)
            )
        else:
            self.remaining_minutes = None
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

    def post(self, request, *args, **kwargs):
        # Handle onboarding completion
        if request.POST.get('complete_onboarding'):
            onboarding_key = f'onboarding_seen_{self.session.uuid}'
            request.session[onboarding_key] = True
            return redirect(self.request.path)

        # Continue with normal form handling
        return super().post(request, *args, **kwargs)

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
                    "candidate:behavioral-pause", args=[self.session.uuid]
                ),
                "last_saved_at": self.session.last_activity_at,
                "guidance_tip": BEHAVIORAL_GUIDANCE,
                "switch_device_url": reverse(
                    "candidate:behavioral-send-link", args=[self.session.uuid]
                ),
                "help_topics": DEFAULT_HELP_TOPICS,
                "practice_url": reverse(
                    "candidate:session-practice", args=[self.session.uuid]
                ),
            }
        )

        # Add onboarding logic
        onboarding_key = f'onboarding_seen_{self.session.uuid}'
        show_onboarding = (
            self.current_index == 0 and  # First question
            not self.request.session.get(onboarding_key, False)  # Not seen before
        )
        context['show_onboarding'] = show_onboarding

        return context

    def form_valid(self, form):
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


class BehavioralAssessmentPauseView(View):
    """Pause handler for the behavioral inventory."""

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
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
        return redirect("candidate:behavioral-paused", session_uuid=session.uuid)


class BehavioralAssessmentPausedView(TemplateView):
    template_name = "candidate/pause_state.html"

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if self.session.status != "paused":
            return redirect(
                "candidate:behavioral-session", session_uuid=self.session.uuid
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        context["assessment_label"] = "Behavioral Inventory"
        context["paused_at"] = self.session.paused_at
        context["resume_url"] = reverse(
            "candidate:behavioral-resume", args=[self.session.uuid]
        )
        context["last_saved_at"] = self.session.last_activity_at
        return context


class BehavioralAssessmentResumeView(View):
    """Resume handler for behavioral sessions."""

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
        )
        if session.status != "paused":
            return redirect("candidate:behavioral-session", session_uuid=session.uuid)
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
        return redirect("candidate:behavioral-session", session_uuid=session.uuid)


class BehavioralAssessmentSendLinkView(View):
    """Email the behavioral assessment link to an address provided by the candidate."""

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(
            BehavioralAssessmentSession, uuid=kwargs["session_uuid"]
        )
        target_email = (request.POST.get("email") or "").strip()
        try:
            validate_email(target_email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("candidate:behavioral-session", session_uuid=session.uuid)

        resume_link = request.build_absolute_uri(
            reverse("candidate:behavioral-session", args=[session.uuid])
        )
        success, error = send_switch_device_email(
            email=target_email,
            candidate_name=session.candidate_id,
            resume_link=resume_link,
            assessment_label="Behavioral Inventory",
        )
        if success:
            messages.success(
                request,
                f"We emailed the secure link to {target_email}.",
            )
        else:
            messages.error(request, error or "We could not send the link right now.")
        return redirect("candidate:behavioral-session", session_uuid=session.uuid)
