from __future__ import annotations

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

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
            return redirect(
                "candidate:marketing-complete", session_uuid=self.session.uuid
            )
        return redirect(
            "candidate:marketing-session", session_uuid=self.session.uuid
        )


class MarketingAssessmentCompleteView(TemplateView):
    template_name = "candidate/marketing_complete.html"

    def get_context_data(self, **kwargs):
        session = get_object_or_404(
            DigitalMarketingAssessmentSession, uuid=kwargs["session_uuid"]
        )
        context = super().get_context_data(**kwargs)
        context["session"] = session
        return context
