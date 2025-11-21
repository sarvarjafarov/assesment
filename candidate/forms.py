from __future__ import annotations

import json
from django import forms

from assessments.models import Question
from .models import CandidateSupportRequest


class QuestionStepForm(forms.Form):
    """Render a single assessment question (or behavioral block) at a time."""

    def __init__(
        self,
        *args,
        question: Question,
        behavioral_block: dict | None = None,
        existing_behavioral_entries: list | None = None,
        **kwargs,
    ):
        self.question = question
        self.behavioral_block = behavioral_block
        self.behavioral_existing_entries = existing_behavioral_entries or []
        super().__init__(*args, **kwargs)

        if question.question_type == Question.TYPE_SINGLE:
            self.fields["response"] = forms.ChoiceField(
                label=question.prompt,
                choices=self._choice_pairs(question),
                widget=forms.RadioSelect,
                required=True,
            )
        elif question.question_type == Question.TYPE_MULTI:
            self.fields["response"] = forms.MultipleChoiceField(
                label=question.prompt,
                choices=self._choice_pairs(question),
                widget=forms.CheckboxSelectMultiple,
                required=True,
            )
        elif question.question_type == Question.TYPE_SCALE:
            labels = question.metadata.get("scale_labels") or [
                "1",
                "2",
                "3",
                "4",
                "5",
            ]
            self.fields["response"] = forms.ChoiceField(
                label=question.prompt,
                choices=[(label, label) for label in labels],
                widget=forms.RadioSelect,
                required=True,
            )
        elif question.question_type == Question.TYPE_TEXT:
            self.fields["response"] = forms.CharField(
                label=question.prompt,
                widget=forms.Textarea(
                    attrs={
                        "rows": 5,
                        "class": "long-form-input",
                        "data-min-length": 120,
                        "placeholder": "Share a structured response covering context, actions, and outcomes.",
                    }
                ),
                required=True,
            )
        elif question.question_type == Question.TYPE_BEHAVIORAL:
            if not behavioral_block:
                raise ValueError("behavioral_block is required for behavioral questions.")
            self.behavioral_statements = behavioral_block.get("statements", [])
            choices = [
                (statement["id"], f"{statement['id']} · {statement['text']}")
                for statement in self.behavioral_statements
            ]
            self.fields["most_like"] = forms.ChoiceField(
                label="Most like me",
                choices=choices,
                widget=forms.Select(
                    attrs={
                        "class": "behavioral-select",
                    }
                ),
                required=True,
            )
            self.fields["least_like"] = forms.ChoiceField(
                label="Least like me",
                choices=choices,
                widget=forms.Select(
                    attrs={
                        "class": "behavioral-select",
                    }
                ),
                required=True,
            )
        else:
            raise ValueError(f"Unsupported question type: {question.question_type}")

    def clean(self):
        cleaned = super().clean()
        if self.question.question_type == Question.TYPE_BEHAVIORAL:
            most = cleaned.get("most_like")
            least = cleaned.get("least_like")
            if most and least and most == least:
                self.add_error(
                    "least_like", "Please choose a different statement for least like me."
                )
            if most and least:
                combined = list(self.behavioral_existing_entries)
                combined.append({"statement_id": most, "response_type": "most_like_me"})
                combined.append({"statement_id": least, "response_type": "least_like_me"})
                cleaned["behavioral_responses"] = combined
        return cleaned

    def to_answer(self) -> dict:
        payload = {"question_id": self.question.id}
        if self.question.question_type == Question.TYPE_SINGLE:
            payload["choice_ids"] = [int(self.cleaned_data["response"])]
        elif self.question.question_type == Question.TYPE_MULTI:
            payload["choice_ids"] = [int(val) for val in self.cleaned_data["response"]]
        elif self.question.question_type in {
            Question.TYPE_TEXT,
            Question.TYPE_SCALE,
        }:
            payload["answer_text"] = self.cleaned_data["response"]
        elif self.question.question_type == Question.TYPE_BEHAVIORAL:
            responses = self.cleaned_data.get("behavioral_responses") or []
            payload["behavioral_responses"] = responses
            payload["answer_text"] = json.dumps(responses)
        return payload

    @staticmethod
    def _choice_pairs(question: Question) -> list[tuple[int, str]]:
        return [(choice.id, choice.label) for choice in question.choices.all()]


class CandidateFeedbackForm(forms.Form):
    score = forms.ChoiceField(
        label="How was this assessment experience?",
        choices=[
            (5, "Excellent"),
            (4, "Good"),
            (3, "Neutral"),
            (2, "Challenging"),
            (1, "Poor"),
        ],
        widget=forms.RadioSelect,
        required=True,
    )
    comment = forms.CharField(
        label="Anything we should know?",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
    contact_email = forms.EmailField(
        label="Email for follow-up (optional)",
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    contact_phone = forms.CharField(
        label="Phone or chat handle (optional)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "+1 555 123 4567"}),
    )
    allow_follow_up = forms.BooleanField(
        label="The recruiting team may contact me about this feedback.",
        required=False,
    )


class CandidateSupportRequestForm(forms.Form):
    topic = forms.ChoiceField(
        label="What do you need help with?",
        choices=CandidateSupportRequest.TOPIC_CHOICES,
        required=True,
    )
    message = forms.CharField(
        label="Describe the issue",
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Tell us what you’re seeing or any blockers."}
        ),
        required=True,
    )
    contact_method = forms.ChoiceField(
        label="Preferred contact method",
        choices=CandidateSupportRequest.CONTACT_METHOD_CHOICES,
        required=True,
    )
    contact_value = forms.CharField(
        label="Where can we reach you?",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "you@example.com or +1 555 123 4567"}),
    )

    def clean(self):
        cleaned = super().clean()
        contact_value = cleaned.get("contact_value", "").strip()
        if not contact_value:
            self.add_error(
                "contact_value",
                "Share an email, phone, or handle so we can reply.",
            )
        else:
            cleaned["contact_value"] = contact_value
        return cleaned
