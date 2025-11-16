from __future__ import annotations

from django import forms

from .models import ProductQuestion


class ProductQuestionForm(forms.Form):
    """Render a single product management question."""

    def __init__(self, *args, question: ProductQuestion, **kwargs):
        self.question = question
        super().__init__(*args, **kwargs)
        q_type = question.question_type
        options = question.options or {}
        self.ranking_items = []
        if q_type in {ProductQuestion.TYPE_MULTIPLE, ProductQuestion.TYPE_SCENARIO}:
            choices = [
                (choice["id"], choice["text"])
                for choice in options.get("choices", [])
            ]
            self.fields["answer"] = forms.ChoiceField(
                label="",
                choices=choices,
                widget=forms.RadioSelect,
            )
        elif q_type == ProductQuestion.TYPE_RANKING:
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
        elif q_type in {
            ProductQuestion.TYPE_BEHAVIORAL_MOST,
            ProductQuestion.TYPE_BEHAVIORAL_LEAST,
        }:
            statements = options.get("statements", [])
            choices = [(str(idx), text) for idx, text in enumerate(statements)]
            self.fields["selected"] = forms.ChoiceField(
                label="",
                choices=choices,
                widget=forms.RadioSelect,
            )
        elif q_type == ProductQuestion.TYPE_REASONING:
            self.fields["answer"] = forms.CharField(
                label="",
                widget=forms.Textarea(
                    attrs={
                        "rows": 5,
                        "placeholder": "Briefly explain your reasoning or approach.",
                    }
                ),
            )
        else:
            self.fields["answer"] = forms.CharField(
                label="",
                widget=forms.Textarea(attrs={"rows": 3}),
            )

    def to_response(self) -> dict:
        payload = {"question_id": self.question.id}
        if "answer" in self.cleaned_data:
            payload["answer"] = self.cleaned_data["answer"]
        if "selected" in self.cleaned_data:
            payload["selected"] = self.cleaned_data["selected"]
        return payload
