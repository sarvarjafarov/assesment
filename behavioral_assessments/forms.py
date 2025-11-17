from __future__ import annotations

from django import forms

from .models import BehavioralQuestion


class BehavioralQuestionForm(forms.Form):
    """Render a behavioural block requesting most/least selections."""

    def __init__(self, *args, question: BehavioralQuestion, **kwargs):
        self.question = question
        super().__init__(*args, **kwargs)
        statements = question.statements or []
        choices = [
            (statement["id"], f"{statement['id']} · {statement['text']}")
            for statement in statements
        ]
        self.fields["most_like"] = forms.ChoiceField(
            label="Most like me",
            choices=choices,
            widget=forms.Select(attrs={"class": "behavioral-select"}),
        )
        self.fields["least_like"] = forms.ChoiceField(
            label="Least like me",
            choices=choices,
            widget=forms.Select(attrs={"class": "behavioral-select"}),
        )

    def clean(self):
        cleaned = super().clean()
        most = cleaned.get("most_like")
        least = cleaned.get("least_like")
        if most and least and most == least:
            self.add_error(
                "least_like",
                "Select a different statement for least like me.",
            )
        return cleaned

    def to_response(self) -> dict:
        return {
            "question_id": self.question.id,
            "most_like": self.cleaned_data.get("most_like"),
            "least_like": self.cleaned_data.get("least_like"),
        }
