from __future__ import annotations

import json

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from assessments.behavioral import get_behavioral_blocks
from assessments.models import AssessmentSession, Question
from assessments.services import record_responses
from .forms import QuestionStepForm


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

    def base_context(self):
        return {
            "session": self.session,
            "assessment": self.session.assessment,
            "candidate": self.session.candidate,
            "instructions": self.session.notes,
            "due_at": self.session.due_at,
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
        return context


class SessionAssessmentView(SessionMixin, FormView):
    template_name = "candidate/session.html"
    form_class = QuestionStepForm

    def dispatch(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        if self.session.status == "completed":
            return redirect(
                "candidate:session-complete", session_uuid=self.session.uuid
            )
        self._ensure_started()
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
            self.session.status = "in_progress"
            if not self.session.started_at:
                self.session.started_at = timezone.now()
            self.session.save(update_fields=["status", "started_at", "updated_at"])

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
        return context

    def form_valid(self, form):
        answers = [form.to_answer()]
        is_final_step = self._is_final_step()
        record_responses(
            session=self.session,
            answers=answers,
            mark_completed=is_final_step,
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
