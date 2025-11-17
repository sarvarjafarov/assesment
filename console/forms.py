from __future__ import annotations

from django import forms

from behavioral_assessments.models import BehavioralAssessmentSession
from behavioral_assessments.services import generate_question_set as generate_behavioral_question_set
from marketing_assessments.models import DigitalMarketingAssessmentSession
from marketing_assessments.services import generate_question_set as generate_marketing_question_set
from pm_assessments.models import ProductAssessmentSession
from pm_assessments.services import generate_question_set as generate_pm_question_set


class MarketingAssessmentInviteForm(forms.Form):
    candidate_identifier = forms.CharField(
        label="Candidate identifier (email or ID)",
        help_text="Used to generate the marketing assessment link.",
    )
    duration_minutes = forms.IntegerField(
        label="Duration (minutes)",
        initial=30,
        min_value=5,
    )

    def clean(self):
        cleaned = super().clean()
        question_set = generate_marketing_question_set()
        if not question_set:
            raise forms.ValidationError("No marketing questions are currently active.")
        self.question_set = question_set
        return cleaned

    def save(self) -> DigitalMarketingAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        session, _ = DigitalMarketingAssessmentSession.objects.get_or_create(
            candidate_id=candidate_id, defaults={"status": "draft"}
        )
        session.question_set = getattr(self, "question_set", None) or generate_marketing_question_set()
        session.status = "in_progress"
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.save(update_fields=["question_set", "status", "duration_minutes", "started_at"])
        return session


class ProductAssessmentInviteForm(forms.Form):
    candidate_identifier = forms.CharField(
        label="Candidate identifier (email or ID)",
        help_text="Used to generate the PM assessment link.",
    )
    duration_minutes = forms.IntegerField(label="Duration (minutes)", initial=30, min_value=5)

    def clean(self):
        cleaned = super().clean()
        question_set = generate_pm_question_set()
        if not question_set:
            raise forms.ValidationError(
                "No PM questions are available yet. Add product questions before creating sessions."
            )
        self.question_set = question_set
        return cleaned

    def save(self) -> ProductAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        session, _ = ProductAssessmentSession.objects.get_or_create(
            candidate_id=candidate_id, defaults={"status": "draft"}
        )
        question_set = getattr(self, "question_set", None) or generate_pm_question_set()
        session.question_set = question_set
        session.status = "in_progress"
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.save(
            update_fields=["question_set", "status", "duration_minutes", "started_at"]
        )
        return session


class BehavioralAssessmentInviteForm(forms.Form):
    candidate_identifier = forms.CharField(
        label="Candidate identifier (email or ID)",
        help_text="Used to generate the behavioral assessment link.",
    )
    duration_minutes = forms.IntegerField(label="Duration (minutes)", initial=15, min_value=5)

    def clean(self):
        cleaned = super().clean()
        question_set = generate_behavioral_question_set()
        if not question_set:
            raise forms.ValidationError("No behavioral blocks are active right now.")
        self.question_set = question_set
        return cleaned

    def save(self) -> BehavioralAssessmentSession:
        candidate_id = self.cleaned_data["candidate_identifier"]
        session, _ = BehavioralAssessmentSession.objects.get_or_create(
            candidate_id=candidate_id, defaults={"status": "draft"}
        )
        question_set = getattr(self, "question_set", None) or generate_behavioral_question_set()
        session.question_set = question_set
        session.status = "in_progress"
        session.duration_minutes = self.cleaned_data["duration_minutes"]
        session.started_at = None
        session.save(
            update_fields=["question_set", "status", "duration_minutes", "started_at"]
        )
        return session
