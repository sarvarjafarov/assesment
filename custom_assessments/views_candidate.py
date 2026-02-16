"""
Candidate-facing views for custom assessments.
"""
from __future__ import annotations

import json
from datetime import timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView

from candidate.constants import DEFAULT_HELP_TOPICS
from candidate.forms import CandidateFeedbackForm

from .forms import (
    CandidateAnswerForm,
    CandidateFileUploadForm,
    CandidateTextResponseForm,
    CandidateVideoResponseForm,
)
from .models import CandidateResponse, CustomAssessmentSession, CustomQuestion
from .services import send_completion_notification


class CustomAssessmentIntroView(TemplateView):
    """Onboarding page shown before candidates start the assessment."""

    template_name = "custom_assessments/candidate_intro.html"

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            CustomAssessmentSession, uuid=kwargs["session_uuid"]
        )

        # Redirect if already submitted
        if self.session.status == "submitted":
            return redirect(
                "candidate:custom-complete", session_uuid=self.session.uuid
            )

        # Check deadline
        if self.session.deadline_at and timezone.now() > self.session.deadline_at:
            return redirect(
                "candidate:custom-expired", session_uuid=self.session.uuid
            )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        context["assessment"] = self.session.assessment
        context["total_questions"] = self.session.assessment.questions.count()
        context["has_started"] = self.session.started_at is not None

        # Check deadline
        if self.session.deadline_at:
            context["is_past_deadline"] = timezone.now() > self.session.deadline_at

        return context


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
                from clients.services import send_new_candidate_alert, trigger_session_webhook, create_notification
                send_new_candidate_alert(
                    self.session.client, self.session, "custom"
                )
                create_notification(
                    self.session.client,
                    "candidate_started",
                    "New Candidate Started",
                    message=f"{self.session.candidate_id} started the Custom Assessment",
                    link_url=reverse('clients:assessment-manage', kwargs={'assessment_type': 'custom'}),
                )
                # Trigger webhook for session started
                trigger_session_webhook(self.session, "session.started")

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
            self.remaining_seconds = max(0, int((deadline - now).total_seconds()))
            self.remaining_minutes = max(0, int(self.remaining_seconds // 60))
        else:
            self.remaining_seconds = None
            self.remaining_minutes = None

        # Get current question
        self.current_index = self.session.current_question_index
        if self.current_index >= len(self.session.question_order):
            self.session.submit()

            # Trigger AI scoring for text responses
            from .services import trigger_ai_scoring_for_session
            trigger_ai_scoring_for_session(self.session)

            # Send completion notification to client
            results_url = request.build_absolute_uri(
                reverse("custom_assessments:session-result", args=[self.session.uuid])
            )
            send_completion_notification(self.session, results_url)

            # Trigger webhook for session completed
            if self.session.client:
                from clients.services import trigger_session_webhook
                trigger_session_webhook(self.session, "session.completed")

            return redirect(
                "candidate:custom-complete", session_uuid=self.session.uuid
            )

        question_id = self.session.question_order[self.current_index]
        self.current_question = get_object_or_404(CustomQuestion, pk=question_id)

        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        """Return the appropriate form class based on question type."""
        qtype = self.current_question.question_type
        if qtype == CustomQuestion.TYPE_MULTIPLE_CHOICE:
            return CandidateAnswerForm
        elif qtype in (CustomQuestion.TYPE_TEXT_SHORT, CustomQuestion.TYPE_TEXT_LONG):
            return CandidateTextResponseForm
        elif qtype == CustomQuestion.TYPE_VIDEO:
            return CandidateVideoResponseForm
        elif qtype == CustomQuestion.TYPE_FILE_UPLOAD:
            return CandidateFileUploadForm
        return CandidateAnswerForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["question"] = self.current_question
        # Include files for video/file uploads
        if self.current_question.question_type in (
            CustomQuestion.TYPE_VIDEO,
            CustomQuestion.TYPE_FILE_UPLOAD,
        ):
            kwargs["files"] = self.request.FILES
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = len(self.session.question_order)

        assessment = self.session.assessment
        context.update(
            {
                "session": self.session,
                "assessment": assessment,
                "question": self.current_question,
                "question_type": self.current_question.question_type,
                "step_number": self.current_index + 1,
                "total_steps": total,
                "progress_percent": int((self.current_index / total) * 100),
                "remaining_minutes": self.remaining_minutes,
                "remaining_seconds": self.remaining_seconds,
                "help_topics": DEFAULT_HELP_TOPICS,
                # Anti-cheating settings
                "anti_cheat": {
                    "require_fullscreen": assessment.require_fullscreen,
                    "detect_tab_switches": assessment.detect_tab_switches,
                    "prevent_copy_paste": assessment.prevent_copy_paste,
                    "max_tab_switches": assessment.max_tab_switches,
                },
                # Question type constants for template
                "TYPE_MULTIPLE_CHOICE": CustomQuestion.TYPE_MULTIPLE_CHOICE,
                "TYPE_TEXT_SHORT": CustomQuestion.TYPE_TEXT_SHORT,
                "TYPE_TEXT_LONG": CustomQuestion.TYPE_TEXT_LONG,
                "TYPE_VIDEO": CustomQuestion.TYPE_VIDEO,
                "TYPE_FILE_UPLOAD": CustomQuestion.TYPE_FILE_UPLOAD,
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
                "candidate:custom-expired", session_uuid=self.session.uuid
            )

        qtype = self.current_question.question_type

        # Handle response based on question type
        if qtype == CustomQuestion.TYPE_MULTIPLE_CHOICE:
            # Multiple choice - store in session.answers
            answer = form.cleaned_data["answer"]
            self.session.record_answer(self.current_question.pk, answer)

        elif qtype in (CustomQuestion.TYPE_TEXT_SHORT, CustomQuestion.TYPE_TEXT_LONG):
            # Text response - store in CandidateResponse
            text_response = form.cleaned_data["text_response"]
            CandidateResponse.objects.update_or_create(
                session=self.session,
                question=self.current_question,
                defaults={"text_response": text_response},
            )

        elif qtype == CustomQuestion.TYPE_VIDEO:
            # Video response - store in CandidateResponse
            video_file = form.cleaned_data.get("video_file")
            if video_file:
                CandidateResponse.objects.update_or_create(
                    session=self.session,
                    question=self.current_question,
                    defaults={"video_file": video_file},
                )

        elif qtype == CustomQuestion.TYPE_FILE_UPLOAD:
            # File upload - store in CandidateResponse
            uploaded_file = form.cleaned_data.get("uploaded_file")
            if uploaded_file:
                CandidateResponse.objects.update_or_create(
                    session=self.session,
                    question=self.current_question,
                    defaults={
                        "uploaded_file": uploaded_file,
                        "uploaded_file_name": uploaded_file.name,
                    },
                )

        # Move to next question
        self.session.current_question_index += 1
        self.session.save(update_fields=["current_question_index", "updated_at"])

        # Check if assessment is complete
        if self.session.current_question_index >= len(self.session.question_order):
            self.session.submit()

            # Trigger AI scoring for text responses
            from .services import trigger_ai_scoring_for_session
            trigger_ai_scoring_for_session(self.session)

            # Send completion notification to client
            results_url = self.request.build_absolute_uri(
                reverse("custom_assessments:session-result", args=[self.session.uuid])
            )
            send_completion_notification(self.session, results_url)

            # Trigger webhook for session completed
            if self.session.client:
                from clients.services import trigger_session_webhook
                trigger_session_webhook(self.session, "session.completed")

            return redirect(
                "candidate:custom-complete", session_uuid=self.session.uuid
            )

        return redirect(
            "candidate:custom-start", session_uuid=self.session.uuid
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


@method_decorator(csrf_exempt, name="dispatch")
class TelemetryEventView(View):
    """API endpoint to receive anti-cheating telemetry events from the frontend."""

    def post(self, request, session_uuid):
        session = get_object_or_404(CustomAssessmentSession, uuid=session_uuid)

        # Only log events for in-progress sessions
        if session.status != "in_progress":
            return JsonResponse({"status": "ignored", "reason": "session not active"})

        try:
            data = json.loads(request.body)
            event_type = data.get("event_type")
            details = data.get("details", {})

            if event_type not in (
                "tab_switch",
                "copy_attempt",
                "paste_attempt",
                "fullscreen_exit",
                "fullscreen_enter",
                "right_click",
                "keyboard_shortcut",
            ):
                return JsonResponse({"status": "error", "reason": "invalid event type"}, status=400)

            session.log_telemetry_event(event_type, details)

            return JsonResponse({
                "status": "ok",
                "trust_score": session.trust_score,
                "flagged": session.flagged_for_review,
            })

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "reason": "invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "reason": str(e)}, status=500)
