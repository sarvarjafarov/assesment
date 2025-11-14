from __future__ import annotations

import json
from typing import Iterable

from django import forms

from assessments.behavioral import get_behavioral_blocks
from assessments.models import Question


class AssessmentResponseForm(forms.Form):
    """Dynamic form that renders fields for each question in an assessment."""

    def __init__(self, *args, assessment, **kwargs):
        self.assessment = assessment
        self.questions = (
            assessment.questions.prefetch_related("choices").order_by("order")
        )
        super().__init__(*args, **kwargs)
        self.behavioral_fields: dict[str, dict] = {}
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
            elif question.question_type == Question.TYPE_BEHAVIORAL:
                blocks = self._prepare_behavioral_blocks(field_name, question)
                self.fields[field_name] = forms.CharField(
                    label=question.prompt,
                    widget=forms.HiddenInput,
                    required=False,
                )
                self.fields[field_name].behavioral_blocks = blocks
                self.behavioral_fields[field_name] = {
                    "question": question,
                    "blocks": blocks,
                }
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
            self.fields[field_name].question = question

    def _prepare_behavioral_blocks(self, field_name: str, question: Question) -> list[dict]:
        config = question.metadata.get("behavioral_bank", {})
        block_ids = config.get("blocks")
        blocks = get_behavioral_blocks(block_ids)
        prepared: list[dict] = []
        for block in blocks:
            most_name = self._behavioral_input_name(field_name, block["id"], "most")
            least_name = self._behavioral_input_name(field_name, block["id"], "least")
            prepared.append(
                {
                    "id": block["id"],
                    "statements": block.get("statements", []),
                    "most_name": most_name,
                    "least_name": least_name,
                    "most_value": self.data.get(most_name, "") if self.is_bound else "",
                    "least_value": self.data.get(least_name, "") if self.is_bound else "",
                }
            )
        return prepared

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
            elif question.question_type == Question.TYPE_BEHAVIORAL:
                payload["behavioral_responses"] = value or []
                payload["answer_text"] = json.dumps(value or [])
            else:
                payload["answer_text"] = value or ""
            answers.append(payload)
        return answers

    def clean(self):
        cleaned = super().clean()
        for field_name, config in self.behavioral_fields.items():
            selections: list[dict] = []
            errors: list[str] = []
            for block in config["blocks"]:
                most_name = block["most_name"]
                least_name = block["least_name"]
                most_value = self.data.get(most_name)
                least_value = self.data.get(least_name)
                valid_ids = {stmt["id"] for stmt in block["statements"]}
                if not most_value or not least_value:
                    errors.append(
                        f"Select both 'Most like me' and 'Least like me' for block {block['id']}."
                    )
                    continue
                if most_value == least_value:
                    errors.append(
                        f"Block {block['id']}: choose different statements for most and least."
                    )
                    continue
                if most_value not in valid_ids or least_value not in valid_ids:
                    errors.append(f"Block {block['id']}: invalid selection.")
                    continue
                selections.append(
                    {"statement_id": most_value, "response_type": "most_like_me"}
                )
                selections.append(
                    {"statement_id": least_value, "response_type": "least_like_me"}
                )
            if errors:
                self.add_error(field_name, " ".join(errors))
            cleaned[field_name] = selections
        return cleaned

    @staticmethod
    def _field_name(question: Question) -> str:
        return f"question_{question.id}"

    @staticmethod
    def _choice_pairs(question: Question) -> list[tuple[int, str]]:
        return [(choice.id, choice.label) for choice in question.choices.all()]

    @staticmethod
    def _behavioral_input_name(field_name: str, block_id: int, kind: str) -> str:
        return f"{field_name}-{block_id}-{kind}"
