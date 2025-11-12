from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django import forms
from django.utils import timezone

from .models import Assessment, AssessmentSession, CandidateProfile, RoleCategory


@dataclass
class InviteResult:
    candidate: CandidateProfile
    session: AssessmentSession
    assessment: Assessment


class AssessmentInviteForm(forms.Form):
    """Capture basic candidate info from landing-page CTA."""

    full_name = forms.CharField(
        max_length=160,
        label="Full name",
        widget=forms.TextInput(attrs={"placeholder": "Jane Candidate"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "talent@example.com"}),
    )
    company = forms.CharField(
        max_length=160,
        required=False,
        label="Company Name",
        widget=forms.TextInput(attrs={"placeholder": "Company Name"}),
    )
    focus_area = forms.ModelChoiceField(
        queryset=RoleCategory.objects.none(),
        label="Assessment Focus",
        empty_label=None,
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Optional notes"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["focus_area"].queryset = RoleCategory.objects.filter(is_active=True)
        if not self.initial.get("focus_area"):
            first_category = self.fields["focus_area"].queryset.first()
            if first_category:
                self.initial["focus_area"] = first_category.pk
                self.fields["focus_area"].initial = first_category.pk

    def save(self, invited_by: str = "Marketing site CTA") -> InviteResult:
        if not self.is_valid():
            raise ValueError("Attempted to save invalid form")

        category: RoleCategory = self.cleaned_data["focus_area"]
        assessment = (
            category.assessments.filter(is_active=True).order_by("title").first()
        )
        if assessment is None:
            raise forms.ValidationError(
                f"No active assessments configured for {category.name} yet."
            )

        first_name, last_name = self._split_name(self.cleaned_data["full_name"])
        candidate, _ = CandidateProfile.objects.update_or_create(
            email=self.cleaned_data["email"].lower(),
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "headline": self.cleaned_data.get("company", ""),
                "metadata": {
                    "company": self.cleaned_data.get("company", ""),
                    "notes": self.cleaned_data.get("notes", ""),
                },
            },
        )

        session, _ = AssessmentSession.objects.get_or_create(
            candidate=candidate,
            assessment=assessment,
            defaults={"status": "invited"},
        )
        session.status = "invited"
        session.invited_by = invited_by
        session.invited_at = timezone.now()
        session.save(update_fields=["status", "invited_by", "invited_at", "updated_at"])

        return InviteResult(candidate=candidate, session=session, assessment=assessment)

    @staticmethod
    def _split_name(full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split(" ", 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ""
        return first, last
