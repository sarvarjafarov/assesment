from __future__ import annotations

from django import forms

from .models import HRQuestion


class HRQuestionForm(forms.Form):
    """Render a single HR assessment question."""

    def __init__(self, *args, question: HRQuestion, **kwargs):
        self.question = question
        super().__init__(*args, **kwargs)
        q_type = question.question_type
        options = question.options or {}
        self.ranking_items = []
        if q_type in {"multiple_choice", "scenario"}:
            choices = [
                (choice["id"], choice["text"])
                for choice in options.get("choices", [])
            ]
            self.fields["answer"] = forms.ChoiceField(
                label="",
                choices=choices,
                widget=forms.RadioSelect,
            )
        elif q_type == "ranking":
            items = options.get("items", [])
            placeholder = ", ".join(items)
            self.fields["answer"] = forms.CharField(
                label="Enter the final order (comma separated)",
                widget=forms.Textarea(
                    attrs={
                        "rows": 3,
                        "placeholder": f"E.g. {placeholder}",
                    }
                ),
            )
            self.ranking_items = items
        elif q_type in {"behavioral_most", "behavioral_least"}:
            statements = options.get("statements", [])
            choices = [(str(idx), text) for idx, text in enumerate(statements)]
            self.fields["selected"] = forms.ChoiceField(
                label="",
                choices=choices,
                widget=forms.RadioSelect,
            )
        elif q_type == "reasoning":
            self.fields["answer"] = forms.CharField(
                label="",
                widget=forms.Textarea(
                    attrs={
                        "rows": 5,
                        "placeholder": "Explain your HR reasoning, approach, and any tradeoffs you considered.",
                        "class": "long-form-input",
                        "data-min-length": 150,
                    }
                ),
            )
        else:
            self.fields["answer"] = forms.CharField(
                label="",
                widget=forms.Textarea(
                    attrs={
                        "rows": 3,
                        "class": "long-form-input",
                        "data-min-length": 150,
                        "placeholder": "Capture your thought process and any tradeoffs you considered.",
                    }
                ),
            )

    def to_response(self) -> dict:
        payload = {"question_id": self.question.id}
        if "answer" in self.cleaned_data:
            payload["answer"] = self.cleaned_data["answer"]
        if "selected" in self.cleaned_data:
            payload["selected"] = self.cleaned_data["selected"]
        return payload
