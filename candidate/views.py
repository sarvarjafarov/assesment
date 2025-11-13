from __future__ import annotations

from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from assessments.models import AssessmentSession
from assessments.services import record_responses
from .forms import AssessmentResponseForm


class SessionEntryView(FormView):
    template_name = "candidate/session.html"
    form_class = AssessmentResponseForm

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            AssessmentSession.objects.select_related(
                "assessment__category", "candidate", "assessment"
            ),
            uuid=kwargs["session_uuid"],
        )
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
        context["session"] = self.session
        context["assessment"] = self.session.assessment
        context["candidate"] = self.session.candidate
        context["is_past_due"] = (
            self.session.due_at and self.session.due_at < timezone.now()
        )
        context["instructions"] = self.session.notes
        return context

    def form_valid(self, form):
        answers = form.to_answers()
        record_responses(session=self.session, answers=answers)
        return redirect("candidate:session-complete", session_uuid=self.session.uuid)


class SessionCompleteView(TemplateView):
    template_name = "candidate/completed.html"

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            AssessmentSession.objects.select_related(
                "assessment__category", "candidate"
            ),
            uuid=kwargs["session_uuid"],
        )
        if self.session.status != "completed":
            return redirect("candidate:session-entry", session_uuid=self.session.uuid)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        context["candidate"] = self.session.candidate
        context["assessment"] = self.session.assessment
        return context
