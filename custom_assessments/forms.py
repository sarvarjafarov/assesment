"""
Forms for Custom Assessments.
"""
from django import forms

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
        choices=[
            ("junior", "Junior (0-2 years experience)"),
            ("mid", "Mid-Level (2-5 years experience)"),
            ("senior", "Senior (5+ years experience)"),
        ],
        initial="mid",
        widget=forms.RadioSelect(attrs={"class": "level-radio"}),
        label="Difficulty Level",
    )
    num_questions = forms.IntegerField(
        min_value=5,
        max_value=30,
        initial=10,
        widget=forms.NumberInput(attrs={
            "class": "form-input",
            "min": 5,
            "max": 30,
        }),
        label="Number of Questions",
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
        choices=[
            ("junior", "Junior (0-2 years)"),
            ("mid", "Mid-Level (2-5 years)"),
            ("senior", "Senior (5+ years)"),
        ],
        initial="mid",
        widget=forms.RadioSelect(attrs={"class": "level-radio"}),
        label="Assessment Level",
    )
