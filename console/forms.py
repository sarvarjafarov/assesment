from __future__ import annotations

from django import forms
from django.utils import timezone

from assessments.models import Assessment, AssessmentSession, Choice, Question
from assessments.services import invite_candidate


def _comma_separated(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


class AssessmentForm(forms.ModelForm):
    """Create or edit assessments with a friendly skills field."""

    skills_focus = forms.CharField(
        help_text="Comma separated values (e.g. Paid Media, Analytics).",
        widget=forms.TextInput(attrs={"placeholder": "Skill A, Skill B"}),
    )

    class Meta:
        model = Assessment
        fields = [
            "category",
            "title",
            "slug",
            "summary",
            "level",
            "duration_minutes",
            "skills_focus",
            "scoring_rubric",
            "is_active",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["skills_focus"].initial = ", ".join(
                self.instance.skills_focus or []
            )

    def clean_skills_focus(self):
        return _comma_separated(self.cleaned_data.get("skills_focus", ""))


class QuestionForm(forms.ModelForm):
    """Capture metadata for assessment questions."""

    scale_labels = forms.CharField(
        required=False,
        help_text="Comma separated labels (only used for scale questions).",
        widget=forms.TextInput(attrs={"placeholder": "Low, Medium, High"}),
    )

    class Meta:
        model = Question
        fields = ["prompt", "question_type", "order", "weight"]
        widgets = {
            "prompt": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        metadata = self.instance.metadata if self.instance.pk else {}
        scale_labels = metadata.get("scale_labels")
        if scale_labels:
            self.fields["scale_labels"].initial = ", ".join(scale_labels)

    def save(self, commit=True):
        question = super().save(commit=False)
        metadata = question.metadata or {}
        labels = _comma_separated(self.cleaned_data.get("scale_labels", ""))
        if labels:
            metadata["scale_labels"] = labels
        else:
            metadata.pop("scale_labels", None)
        question.metadata = metadata
        if commit:
            question.save()
        return question


class ChoiceForm(forms.ModelForm):
    """Form to add choices for single or multi-select questions."""

    class Meta:
        model = Choice
        fields = ["label", "value", "weight"]
        widgets = {
            "label": forms.TextInput(attrs={"placeholder": "Option label"}),
            "value": forms.TextInput(attrs={"placeholder": "Optional value"}),
        }


class ConsoleInviteForm(forms.Form):
    """Invite a candidate to an assessment with an optional due date."""

    full_name = forms.CharField(label="Candidate name")
    email = forms.EmailField()
    company = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Company or team"}),
    )
    assessment = forms.ModelChoiceField(
        queryset=Assessment.objects.filter(is_active=True).order_by("title"),
        empty_label=None,
    )
    due_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text="Optional deadline (local time).",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Expectation, context, etc."}
        ),
    )

    def clean_due_at(self):
        due_at = self.cleaned_data.get("due_at")
        if due_at and timezone.is_naive(due_at):
            due_at = timezone.make_aware(due_at, timezone.get_current_timezone())
        return due_at

    def save(self, invited_by: str):
        full_name = self.cleaned_data["full_name"].strip()
        first_name, last_name = _split_name(full_name)
        assessment: Assessment = self.cleaned_data["assessment"]
        result = invite_candidate(
            assessment=assessment,
            first_name=first_name,
            last_name=last_name,
            email=self.cleaned_data["email"],
            headline=self.cleaned_data.get("company", ""),
            metadata={
                "company": self.cleaned_data.get("company", ""),
                "notes": self.cleaned_data.get("notes", ""),
            },
            invited_by=invited_by,
        )
        session = result.session
        session.notes = self.cleaned_data.get("notes", "")
        session.due_at = self.cleaned_data.get("due_at")
        session.save(update_fields=["notes", "due_at", "updated_at"])
        return result


class SessionUpdateForm(forms.ModelForm):
    """Allow talent teams to update status, deadlines, and notes."""

    due_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = AssessmentSession
        fields = ["status", "decision", "decision_notes", "due_at", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "decision_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (
            not self.is_bound
            and self.instance
            and self.instance.pk
            and self.instance.due_at
        ):
            local_value = timezone.localtime(self.instance.due_at)
            self.initial["due_at"] = local_value.strftime("%Y-%m-%dT%H:%M")

    def clean_due_at(self):
        due_at = self.cleaned_data.get("due_at")
        if due_at and timezone.is_naive(due_at):
            due_at = timezone.make_aware(due_at, timezone.get_current_timezone())
        return due_at


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split(" ", 1)
    first = parts[0] if parts else "Candidate"
    last = parts[1] if len(parts) > 1 else ""
    return first, last
