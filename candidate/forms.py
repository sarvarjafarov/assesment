from __future__ import annotations

from typing import Iterable

from django import forms

from assessments.models import Question


class AssessmentResponseForm(forms.Form):
    """Dynamic form that renders fields for each question in an assessment."""

    def __init__(self, *args, assessment, **kwargs):
        self.assessment = assessment
        self.questions = (
            assessment.questions.prefetch_related("choices").order_by("order")
        )
        super().__init__(*args, **kwargs)
        for question in self.questions:
            field_name = self._field_name(question)
            if question.question_type == Question.TYPE_SINGLE:
                self.fields[field_name] = forms.ChoiceField(
                    label=question.prompt,
                    choices=self._choice_pairs(question),
                    widget=forms.RadioSelect,
                    required=True,
                )
            elif question.question_type == Question.TYPE_MULTI:
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=question.prompt,
                    choices=self._choice_pairs(question),
                    widget=forms.CheckboxSelectMultiple,
                    required=False,
                )
            elif question.question_type == Question.TYPE_SCALE:
                labels = question.metadata.get("scale_labels") or [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                ]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.prompt,
                    choices=[(label, label) for label in labels],
                    widget=forms.RadioSelect,
                    required=True,
                )
            else:
                self.fields[field_name] = forms.CharField(
                    label=question.prompt,
                    widget=forms.Textarea(attrs={"rows": 4}),
                    required=True,
                )

    def to_answers(self) -> list[dict]:
        """Transform cleaned_data into the payload expected by record_responses."""

        answers: list[dict] = []
        for question in self.questions:
            field_name = self._field_name(question)
            value = self.cleaned_data.get(field_name)
            payload = {"question_id": question.id}
            if question.question_type == Question.TYPE_SINGLE:
                payload["choice_ids"] = [int(value)] if value else []
            elif question.question_type == Question.TYPE_MULTI:
                payload["choice_ids"] = [int(val) for val in value]
            else:
                payload["answer_text"] = value or ""
            answers.append(payload)
        return answers

    @staticmethod
    def _field_name(question: Question) -> str:
        return f"question_{question.id}"

    @staticmethod
    def _choice_pairs(question: Question) -> list[tuple[int, str]]:
        return [(choice.id, choice.label) for choice in question.choices.all()]

