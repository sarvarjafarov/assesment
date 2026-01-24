"""
Forms for Custom Assessments.
"""
from django import forms

from .constants import LEVEL_CHOICES
from .models import CustomAssessment, CustomQuestion


class CustomAssessmentForm(forms.ModelForm):
    """Form for creating/editing custom assessments."""

    class Meta:
        model = CustomAssessment
        fields = ["name", "description", "time_limit_minutes", "passing_score"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g., Sales Representative Assessment",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Describe what this assessment tests...",
            }),
            "time_limit_minutes": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 5,
                "max": 120,
            }),
            "passing_score": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "max": 100,
            }),
        }
        labels = {
            "name": "Assessment Name",
            "description": "Description",
            "time_limit_minutes": "Time Limit (minutes)",
            "passing_score": "Passing Score (%)",
        }


class AIGenerationForm(forms.Form):
    """Form for AI-based question generation."""

    role_description = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "e.g., Senior Sales Representative",
        }),
        label="Role/Position",
        help_text="The job role this assessment is for",
    )
    skills_to_test = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-textarea",
            "rows": 3,
            "placeholder": "e.g., cold calling, objection handling, CRM usage, closing techniques",
        }),
        label="Skills to Test",
        help_text="Comma-separated list of skills and knowledge areas",
    )
    difficulty_level = forms.ChoiceField(
        choices=LEVEL_CHOICES,
        initial="mid",
        widget=forms.RadioSelect(attrs={"class": "level-radio"}),
        label="Difficulty Level",
    )
    num_questions = forms.IntegerField(
        min_value=5,
        max_value=10,
        initial=5,
        widget=forms.NumberInput(attrs={
            "class": "form-input",
            "min": 5,
            "max": 10,
        }),
        label="Number of Questions",
        help_text="5-10 questions per batch (generate multiple batches for more)",
    )


class CSVUploadForm(forms.Form):
    """Form for CSV file upload."""

    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            "class": "form-file-input",
            "accept": ".csv",
        }),
        label="CSV File",
        help_text="Upload a CSV file with your questions",
    )

    def clean_csv_file(self):
        file = self.cleaned_data["csv_file"]

        # Check file extension
        if not file.name.endswith(".csv"):
            raise forms.ValidationError("File must be a CSV file (.csv)")

        # Check file size (max 1MB)
        if file.size > 1024 * 1024:
            raise forms.ValidationError("File size must be less than 1MB")

        return file


class CustomQuestionForm(forms.ModelForm):
    """Form for creating/editing individual questions."""

    class Meta:
        model = CustomQuestion
        fields = [
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "explanation",
            "difficulty_level",
            "category",
        ]
        widgets = {
            "question_text": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Enter your question here...",
            }),
            "option_a": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Option A",
            }),
            "option_b": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Option B",
            }),
            "option_c": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Option C (optional)",
            }),
            "option_d": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Option D (optional)",
            }),
            "correct_answer": forms.Select(
                choices=[
                    ("A", "A"),
                    ("B", "B"),
                    ("C", "C"),
                    ("D", "D"),
                ],
                attrs={"class": "form-select"},
            ),
            "explanation": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2,
                "placeholder": "Explain why this is the correct answer...",
            }),
            "difficulty_level": forms.Select(
                choices=[
                    (1, "1 - Very Easy"),
                    (2, "2 - Easy"),
                    (3, "3 - Medium"),
                    (4, "4 - Hard"),
                    (5, "5 - Very Hard"),
                ],
                attrs={"class": "form-select"},
            ),
            "category": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g., Technical, Communication",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        correct = cleaned_data.get("correct_answer")
        option_c = cleaned_data.get("option_c")
        option_d = cleaned_data.get("option_d")

        if correct == "C" and not option_c:
            self.add_error("option_c", "Option C is required when it's the correct answer")
        if correct == "D" and not option_d:
            self.add_error("option_d", "Option D is required when it's the correct answer")

        return cleaned_data


class CandidateAnswerForm(forms.Form):
    """Form for candidates answering a multiple choice question."""

    answer = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={"class": "option-radio"}),
        label="",
    )

    def __init__(self, *args, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        if question:
            self.question = question
            # Build choices from question options
            choices = [
                ("A", question.option_a),
                ("B", question.option_b),
            ]
            if question.option_c:
                choices.append(("C", question.option_c))
            if question.option_d:
                choices.append(("D", question.option_d))
            self.fields["answer"].choices = choices


class InviteCandidateForm(forms.Form):
    """Form for inviting candidates to a custom assessment."""

    candidate_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-input",
            "placeholder": "candidate@example.com",
        }),
        label="Candidate Email",
    )
    candidate_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "e.g., John Smith or candidate reference",
        }),
        label="Candidate Name/ID",
    )
    level = forms.ChoiceField(
        choices=LEVEL_CHOICES,
        initial="mid",
        widget=forms.RadioSelect(attrs={"class": "level-radio"}),
        label="Assessment Level",
    )
    deadline_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            "class": "form-input",
            "type": "datetime-local",
        }),
        label="Deadline (Optional)",
        help_text="Set a deadline for the candidate to complete the assessment",
    )
    project = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Project (Optional)",
    )

    def __init__(self, *args, client_account=None, **kwargs):
        super().__init__(*args, **kwargs)
        if client_account:
            from clients.models import ClientProject
            projects = ClientProject.objects.filter(
                client_account=client_account,
                is_active=True
            ).order_by("name")
            choices = [("", "— No Project —")]
            choices.extend([(str(p.pk), p.name) for p in projects])
            self.fields["project"].choices = choices


class BulkInviteForm(forms.Form):
    """Form for bulk inviting candidates via CSV."""

    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            "class": "form-file-input",
            "accept": ".csv",
        }),
        label="CSV File",
        help_text="CSV with columns: name, email (one candidate per row)",
    )
    level = forms.ChoiceField(
        choices=LEVEL_CHOICES,
        initial="mid",
        widget=forms.RadioSelect(attrs={"class": "level-radio"}),
        label="Assessment Level",
    )
    deadline_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            "class": "form-input",
            "type": "datetime-local",
        }),
        label="Deadline (Optional)",
    )

    def clean_csv_file(self):
        file = self.cleaned_data["csv_file"]
        if not file.name.endswith(".csv"):
            raise forms.ValidationError("File must be a CSV file (.csv)")
        if file.size > 1024 * 1024:  # 1MB limit
            raise forms.ValidationError("File size must be less than 1MB")
        return file
