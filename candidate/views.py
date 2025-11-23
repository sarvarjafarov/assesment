from __future__ import annotations

import json

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from assessments.behavioral import get_behavioral_blocks
from assessments.models import AssessmentSession, Question
from assessments.services import record_responses
from .constants import DEFAULT_HELP_TOPICS, PRACTICE_QUESTIONS
from .forms import QuestionStepForm, CandidateSupportRequestForm
from .models import CandidateSupportRequest
from .utils import (
    notify_support_team,
    send_switch_device_email,
    update_session_telemetry,
)


DEFAULT_PREVIEW_MIN_CHARS = 120
QUESTION_GUIDANCE = {
    Question.TYPE_SINGLE: {
        "title": "Single best answer",
        "body": "Choose the strongest option. We only record one selection per question.",
    },
    Question.TYPE_MULTI: {
        "title": "Select all that apply",
        "body": "Check every option that fits. Partial credit is awarded for solid coverage.",
    },
    Question.TYPE_SCALE: {
        "title": "Scale response",
        "body": "Use the full scale and anchor your choice to how confident you feel.",
    },
    Question.TYPE_TEXT: {
        "title": "Structured response",
        "body": "Share the context, the actions you took, and the measurable outcome. Bullet points are fine.",
    },
    Question.TYPE_BEHAVIORAL: {
        "title": "Behavioral block",
        "body": "Pick one statement that is most like you and another that is least like you. Each must be unique.",
    },
}

LONGFORM_PREVIEW_TYPES = {Question.TYPE_TEXT}


class SessionMixin:
    """Shared helpers for candidate session views."""

    session: AssessmentSession

    def dispatch(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        return super().dispatch(request, *args, **kwargs)

    def load_session(self, **kwargs):
        if hasattr(self, "session"):
            return
        self.session = get_object_or_404(
            AssessmentSession.objects.select_related(
                "assessment__category", "candidate", "assessment"
            ),
            uuid=kwargs["session_uuid"],
        )
        self.support_form_storage_key = f"support_form_data:{self.session.uuid}"

    def base_context(self):
        return {
            "session": self.session,
            "assessment": self.session.assessment,
            "candidate": self.session.candidate,
            "instructions": self.session.notes,
            "due_at": self.session.due_at,
            "behavioral_focus_traits": self.session.behavioral_focus_traits,
            "behavioral_focus_label": self.session.behavioral_focus_display,
            "last_saved_at": self.session.last_activity_at,
            "help_topics": DEFAULT_HELP_TOPICS,
        }


class SessionIntroView(SessionMixin, TemplateView):
    template_name = "candidate/intro.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.base_context())
        context["start_url"] = reverse(
            "candidate:session-start", args=[self.session.uuid]
        )
        context["is_past_due"] = (
            self.session.due_at and self.session.due_at < timezone.now()
        )
        context["has_started"] = self.session.status in {"in_progress", "completed"}
        context["is_paused"] = self.session.status == "paused"
        context["paused_at"] = self.session.paused_at
        context["resume_url"] = reverse(
            "candidate:session-resume", args=[self.session.uuid]
        )
        context["practice_url"] = reverse(
            "candidate:session-practice", args=[self.session.uuid]
        )
        return context


class SessionAssessmentView(SessionMixin, FormView):
    template_name = "candidate/session.html"
    form_class = QuestionStepForm

    def dispatch(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        if self.session.status == "paused":
            return redirect("candidate:session-paused", session_uuid=self.session.uuid)
        if self.session.status == "completed":
            return redirect(
                "candidate:session-complete", session_uuid=self.session.uuid
            )
        self._ensure_started()
        update_session_telemetry(self.session, request=request)
        self._prepare_questions()
        self._prepare_progress()
        self._determine_current_step()
        if not self.current_question:
            return redirect(
                "candidate:session-complete", session_uuid=self.session.uuid
            )
        return super().dispatch(request, *args, **kwargs)

    def _ensure_started(self):
        if self.session.status in {"draft", "invited"}:
            now = timezone.now()
            self.session.status = "in_progress"
            if not self.session.started_at:
                self.session.started_at = now
            if not self.session.last_activity_at:
                self.session.last_activity_at = now
            self.session.save(
                update_fields=[
                    "status",
                    "started_at",
                    "last_activity_at",
                    "updated_at",
                ]
            )

    def _prepare_questions(self):
        self.questions = list(
            self.session.assessment.questions.prefetch_related("choices").order_by(
                "order"
            )
        )
        self.responses = list(self.session.responses.all())
        self.response_map = {response.question_id: response for response in self.responses}

    def _prepare_progress(self):
        self.total_steps = 0
        self.behavioral_progress: dict[int, dict] = {}
        score_progress = (self.session.score_breakdown or {}).get("behavioral_progress", {})
        for question in self.questions:
            if question.question_type == Question.TYPE_BEHAVIORAL:
                block_ids = (
                    question.metadata.get("behavioral_bank", {}).get("blocks") or []
                )
                self.total_steps += len(block_ids)
                response = self.response_map.get(question.id)
                entries: list[dict] = []
                if response and response.answer_text:
                    try:
                        entries = json.loads(response.answer_text)
                    except json.JSONDecodeError:
                        entries = []
                elif response:
                    entries = response.metadata.get("behavioral_partial", [])
                if str(question.id) in score_progress:
                    entries = score_progress[str(question.id)]
                answered_blocks = min(len(entries) // 2, len(block_ids))
                self.behavioral_progress[question.id] = {
                    "entries": entries,
                    "answered_blocks": answered_blocks,
                    "total_blocks": len(block_ids),
                    "block_ids": block_ids,
                }
            else:
                self.total_steps += 1

    def _determine_current_step(self):
        self.current_question = None
        self.behavioral_block = None
        self.behavioral_existing_entries: list[dict] = []
        self.behavioral_block_index = 0
        self.behavioral_total_blocks = 0
        self.step_index = 0
        steps_completed = 0

        for index, question in enumerate(self.questions):
            if question.question_type == Question.TYPE_BEHAVIORAL:
                progress = self.behavioral_progress.get(
                    question.id,
                    {"entries": [], "answered_blocks": 0, "total_blocks": 0, "block_ids": []},
                )
                answered_blocks = progress["answered_blocks"]
                total_blocks = progress["total_blocks"]
                block_ids = progress["block_ids"]

                if answered_blocks < total_blocks:
                    block_id = (
                        block_ids[answered_blocks] if answered_blocks < len(block_ids) else None
                    )
                    block_data = self._resolve_behavioral_block(block_id)
                    self.current_question = question
                    self.question_index = index
                    self.step_index = steps_completed + answered_blocks
                    self.behavioral_block = block_data
                    self.behavioral_existing_entries = progress["entries"]
                    self.behavioral_block_index = answered_blocks
                    self.behavioral_total_blocks = total_blocks
                    return
                steps_completed += total_blocks
            else:
                if question.id not in self.response_map:
                    self.current_question = question
                    self.question_index = index
                    self.step_index = steps_completed
                    return
                steps_completed += 1

    def _resolve_behavioral_block(self, block_id: int | None) -> dict | None:
        if not block_id:
            return None
        blocks = get_behavioral_blocks([block_id])
        return blocks[0] if blocks else None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["question"] = self.current_question
        if self.current_question.question_type == Question.TYPE_BEHAVIORAL:
            kwargs["behavioral_block"] = self.behavioral_block
            kwargs["existing_behavioral_entries"] = self.behavioral_existing_entries
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.base_context())
        context["is_past_due"] = (
            self.session.due_at and self.session.due_at < timezone.now()
        )
        context["question"] = self.current_question
        context["step_number"] = self.step_index + 1
        context["total_steps"] = max(self.total_steps, 1)
        context["progress_percent"] = int(
            (self.step_index / max(self.total_steps, 1)) * 100
        )
        context["behavioral_block"] = self.behavioral_block
        context["behavioral_block_index"] = (
            self.behavioral_block_index + 1
            if self.current_question.question_type == Question.TYPE_BEHAVIORAL
            else None
        )
        context["behavioral_total_blocks"] = self.behavioral_total_blocks
        context["pause_url"] = reverse(
            "candidate:session-pause", args=[self.session.uuid]
        )
        context["switch_device_url"] = reverse(
            "candidate:session-send-link", args=[self.session.uuid]
        )
        context["practice_url"] = reverse(
            "candidate:session-practice", args=[self.session.uuid]
        )
        context["guidance_tip"] = QUESTION_GUIDANCE.get(
            self.current_question.question_type
        )
        context["show_preview"] = (
            self.current_question.question_type in LONGFORM_PREVIEW_TYPES
        )
        context["preview_min_length"] = DEFAULT_PREVIEW_MIN_CHARS
        support_initial = {
            "contact_method": "email",
            "contact_value": self.session.candidate.email or "",
        }
        stored_support_data = self.request.session.pop(
            getattr(self, "support_form_storage_key", ""), None
        )
        if stored_support_data:
            support_form = CandidateSupportRequestForm(data=stored_support_data)
        else:
            support_form = CandidateSupportRequestForm(initial=support_initial)
        context["support_form"] = support_form
        context["support_contact_email"] = getattr(
            settings, "SUPPORT_CONTACT_EMAIL", "support@evalon.so"
        )
        context["support_contact_phone"] = getattr(
            settings, "SUPPORT_CONTACT_PHONE", "+1 (555) 123-4567"
        )
        context["support_request_url"] = reverse(
            "candidate:session-support-request", args=[self.session.uuid]
        )
        return context

    def form_valid(self, form):
        answers = [form.to_answer()]
        is_final_step = self._is_final_step()
        record_responses(
            session=self.session,
            answers=answers,
            mark_completed=is_final_step,
        )
        update_session_telemetry(
            self.session, payload=self.request.POST.get("telemetry_payload")
        )
        if (
            self.current_question.question_type == Question.TYPE_BEHAVIORAL
            and not is_final_step
        ):
            breakdown = dict(self.session.score_breakdown or {})
            progress = dict(breakdown.get("behavioral_progress", {}))
            progress[str(self.current_question.id)] = form.cleaned_data.get(
                "behavioral_responses", []
            )
            breakdown["behavioral_progress"] = progress
            self.session.score_breakdown = breakdown
            self.session.save(update_fields=["score_breakdown", "updated_at"])
        if is_final_step:
            return redirect("candidate:session-complete", session_uuid=self.session.uuid)
        return redirect("candidate:session-start", session_uuid=self.session.uuid)

    def _is_final_step(self) -> bool:
        return (self.step_index + 1) >= max(self.total_steps, 1)



class SessionCompleteView(SessionMixin, TemplateView):
    template_name = "candidate/completed.html"

    def dispatch(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        if self.session.status != "completed":
            return redirect("candidate:session-start", session_uuid=self.session.uuid)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.base_context())
        return context


class SessionSendLinkView(SessionMixin, View):
    """Email the candidate their secure session URL so they can change devices."""

    def post(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        candidate = self.session.candidate
        resume_link = request.build_absolute_uri(
            reverse("candidate:session-entry", args=[self.session.uuid])
        )
        email_input = (request.POST.get("email") or candidate.email or "").strip()
        if not email_input:
            messages.error(request, "Enter an email address to send your secure link.")
            return redirect("candidate:session-start", session_uuid=self.session.uuid)
        try:
            validate_email(email_input)
        except ValidationError:
            messages.error(request, "That email looks invalid. Please double-check and try again.")
            return redirect("candidate:session-start", session_uuid=self.session.uuid)
        success, error = send_switch_device_email(
            email=email_input,
            candidate_name=candidate.first_name,
            resume_link=resume_link,
            assessment_label=self.session.assessment.title,
        )
        if success:
            messages.success(
                request,
                f"We emailed the secure link to {email_input}.",
            )
        else:
            messages.error(request, error or "We could not send the link right now.")
        return redirect("candidate:session-start", session_uuid=self.session.uuid)


class SessionSupportRequestView(SessionMixin, View):
    """Capture urgent support notes + contact info from candidates."""

    def post(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        form = CandidateSupportRequestForm(request.POST)
        storage_key = getattr(self, "support_form_storage_key", "")
        if not form.is_valid():
            request.session[storage_key] = request.POST.dict()
            messages.error(
                request, "Share a quick note and how we can reach you so we can help."
            )
            return redirect("candidate:session-start", session_uuid=self.session.uuid)
        data = form.cleaned_data
        candidate_obj = self.session.candidate
        candidate_name = " ".join(
            part
            for part in [getattr(candidate_obj, "first_name", ""), getattr(candidate_obj, "last_name", "")]
            if part
        ).strip()
        support_request = CandidateSupportRequest.objects.create(
            session=self.session,
            topic=data["topic"],
            message=data["message"],
            contact_method=data["contact_method"],
            contact_value=data["contact_value"],
            candidate_name=candidate_name,
            candidate_email=getattr(candidate_obj, "email", "") or "",
        )
        subject = f"Candidate support needed ({support_request.get_topic_display()})"
        resume_link = request.build_absolute_uri(
            reverse("candidate:session-entry", args=[self.session.uuid])
        )
        body = (
            f"Session: {self.session.uuid}\n"
            f"Candidate: {support_request.candidate_name or 'N/A'} ({support_request.candidate_email or 'n/a'})\n"
            f"Contact ({support_request.contact_method}): {support_request.contact_value}\n\n"
            f"Message:\n{support_request.message}\n\n"
            f"Resume link: {resume_link}"
        )
        notify_support_team(subject, body)
        messages.success(
            request,
            "Thanks—we’ve routed this to support. Keep an eye on your email/phone for a response.",
        )
        if storage_key in request.session:
            del request.session[storage_key]
        return redirect("candidate:session-start", session_uuid=self.session.uuid)


class SessionPracticeView(SessionMixin, TemplateView):
    template_name = "candidate/practice.html"

    def post(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        context = self.get_context_data(**kwargs)
        mcq_answer = request.POST.get("practice_choice")
        text_answer = request.POST.get("practice_text", "").strip()
        results = {}
        for question in PRACTICE_QUESTIONS:
            if question["type"] == "multiple_choice" and mcq_answer:
                results["multiple_choice"] = mcq_answer == question["answer"]
            if question["type"] == "text" and text_answer:
                results["text"] = len(text_answer.split()) >= 10
        context["practice_results"] = results
        context["submitted_choice"] = mcq_answer
        context["submitted_text"] = text_answer
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.base_context())
        context["practice_questions"] = PRACTICE_QUESTIONS
        context["practice_results"] = context.get("practice_results") or {}
        context["practice_url"] = reverse(
            "candidate:session-practice", args=[self.session.uuid]
        )
        return context


class SessionPauseActionView(SessionMixin, View):
    """Persist a manual pause request and redirect to the pause confirmation view."""

    def post(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        if self.session.status != "completed":
            now = timezone.now()
            self.session.status = "paused"
            self.session.paused_at = now
            self.session.last_activity_at = now
            self.session.save(
                update_fields=[
                    "status",
                    "paused_at",
                    "last_activity_at",
                    "updated_at",
                ]
            )
        return redirect("candidate:session-paused", session_uuid=self.session.uuid)


class SessionPausedView(SessionMixin, TemplateView):
    template_name = "candidate/pause_state.html"

    def dispatch(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        if self.session.status != "paused":
            return redirect("candidate:session-start", session_uuid=self.session.uuid)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.base_context())
        context["paused_at"] = self.session.paused_at
        context["resume_url"] = reverse(
            "candidate:session-resume", args=[self.session.uuid]
        )
        context["assessment_label"] = self.session.assessment.title
        return context


class SessionResumeView(SessionMixin, View):
    """Resume a paused assessment and return the candidate to the next question."""

    def post(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        if self.session.status != "paused":
            return redirect("candidate:session-start", session_uuid=self.session.uuid)
        now = timezone.now()
        paused_seconds = self.session.total_paused_seconds or 0
        if self.session.paused_at:
            paused_seconds += int((now - self.session.paused_at).total_seconds())
        self.session.total_paused_seconds = paused_seconds
        self.session.paused_at = None
        self.session.status = "in_progress"
        self.session.last_activity_at = now
        self.session.save(
            update_fields=[
                "status",
                "paused_at",
                "total_paused_seconds",
                "last_activity_at",
                "updated_at",
            ]
        )
        return redirect("candidate:session-start", session_uuid=self.session.uuid)
