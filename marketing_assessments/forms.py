from __future__ import annotations

from django import forms

from .models import DigitalMarketingQuestion


class MarketingQuestionForm(forms.Form):
    """Render a single digital marketing question."""

    def __init__(self, *args, question: DigitalMarketingQuestion, **kwargs):
        self.question = question
        super().__init__(*args, **kwargs)
        q_type = question.question_type
        options = question.options or {}
        if q_type in {"multiple_choice", "scenario"}:
            choices = [
                (choice["id"], choice["text"])
                for choice in options.get("choices", [])
            ]
            self.fields["answer"] = forms.ChoiceField(
                label=question.question_text,
                choices=choices,
                widget=forms.RadioSelect,
            )
        elif q_type == "ranking":
            items = options.get("items", [])
            placeholder = ", ".join(items)
            self.fields["answer"] = forms.CharField(
                label=question.question_text,
                widget=forms.Textarea(
                    attrs={
                        "rows": 3,
                        "placeholder": f"Enter order separated by commas (e.g. {placeholder})",
                    }
                ),
            )
        elif q_type in {"behavioral_most", "behavioral_least"}:
            statements = options.get("statements", [])
            choices = [(str(idx), text) for idx, text in enumerate(statements)]
            self.fields["selected"] = forms.ChoiceField(
                label="Select the statement that best fits",
                choices=choices,
                widget=forms.RadioSelect,
            )
        else:
            self.fields["answer"] = forms.CharField(
                label=question.question_text,
                widget=forms.Textarea(attrs={"rows": 3}),
            )

    def to_response(self) -> dict:
        payload = {"question_id": self.question.id}
        if "answer" in self.cleaned_data:
            payload["answer"] = self.cleaned_data["answer"]
        if "selected" in self.cleaned_data:
            payload["selected"] = self.cleaned_data["selected"]
        return payload
