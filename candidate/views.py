from __future__ import annotations

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from assessments.models import AssessmentSession
from assessments.services import record_responses
from .forms import AssessmentResponseForm


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
    form_class = AssessmentResponseForm

    def dispatch(self, request, *args, **kwargs):
        self.load_session(**kwargs)
        if self.session.status == "completed":
            return redirect(
                "candidate:session-complete", session_uuid=self.session.uuid
            )
        self._ensure_started()
        return super().dispatch(request, *args, **kwargs)

    def _ensure_started(self):
        if self.session.status in {"draft", "invited"}:
            self.session.status = "in_progress"
            if not self.session.started_at:
                self.session.started_at = timezone.now()
            self.session.save(update_fields=["status", "started_at", "updated_at"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["assessment"] = self.session.assessment
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.base_context())
        context["is_past_due"] = (
            self.session.due_at and self.session.due_at < timezone.now()
        )
        return context

    def form_valid(self, form):
        answers = form.to_answers()
        record_responses(session=self.session, answers=answers)
        return redirect("candidate:session-complete", session_uuid=self.session.uuid)


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
