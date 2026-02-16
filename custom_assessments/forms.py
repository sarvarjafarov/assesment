"""
Forms for Custom Assessments.
"""
from django import forms

from .constants import LEVEL_CHOICES
from .models import CandidateResponse, CustomAssessment, CustomQuestion


class CustomAssessmentForm(forms.ModelForm):
    """Form for creating/editing custom assessments."""

    class Meta:
        model = CustomAssessment
        fields = [
            "name",
            "description",
            "time_limit_minutes",
            "passing_score",
            # Anti-cheating settings
            "require_fullscreen",
            "detect_tab_switches",
            "prevent_copy_paste",
            "max_tab_switches",
        ]
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
            # Anti-cheating widgets
            "require_fullscreen": forms.CheckboxInput(attrs={
                "class": "form-checkbox",
            }),
            "detect_tab_switches": forms.CheckboxInput(attrs={
                "class": "form-checkbox",
            }),
            "prevent_copy_paste": forms.CheckboxInput(attrs={
                "class": "form-checkbox",
            }),
            "max_tab_switches": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "max": 10,
            }),
        }
        labels = {
            "name": "Assessment Name",
            "description": "Description",
            "time_limit_minutes": "Time Limit (minutes)",
            "passing_score": "Passing Score (%)",
            "require_fullscreen": "Require Fullscreen Mode",
            "detect_tab_switches": "Detect Tab Switching",
            "prevent_copy_paste": "Prevent Copy/Paste",
            "max_tab_switches": "Max Tab Switches Before Flagging",
        }
        help_texts = {
            "require_fullscreen": "Force candidates to use fullscreen mode during the assessment",
            "detect_tab_switches": "Track when candidates switch to other tabs or windows",
            "prevent_copy_paste": "Disable copying question text and right-click menu",
            "max_tab_switches": "Flag for review if candidate exceeds this limit (0 = no limit)",
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
        max_value=50,
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
            "question_type",
            "question_text",
            # Multiple choice fields
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            # Text question fields
            "text_min_length",
            "text_max_length",
            "text_ideal_answer",
            # Video question fields
            "video_max_duration_seconds",
            # File upload fields
            "file_allowed_extensions",
            "file_max_size_mb",
            # Common fields
            "explanation",
            "difficulty_level",
            "points",
            "category",
        ]
        widgets = {
            "question_type": forms.Select(attrs={
                "class": "form-select",
                "onchange": "toggleQuestionTypeFields(this.value)",
            }),
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
                    ("", "—"),
                    ("A", "A"),
                    ("B", "B"),
                    ("C", "C"),
                    ("D", "D"),
                ],
                attrs={"class": "form-select"},
            ),
            "text_min_length": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "placeholder": "0",
            }),
            "text_max_length": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 1,
                "placeholder": "5000",
            }),
            "text_ideal_answer": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Reference answer for AI scoring (optional)...",
            }),
            "video_max_duration_seconds": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 10,
                "max": 600,
                "placeholder": "120",
            }),
            "file_allowed_extensions": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "pdf,doc,docx,txt,py,js",
            }),
            "file_max_size_mb": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 1,
                "max": 50,
                "placeholder": "10",
            }),
            "explanation": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2,
                "placeholder": "Explain the expected answer or provide grading hints...",
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
            "points": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 1,
                "max": 10,
            }),
            "category": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g., Technical, Communication",
            }),
        }
        labels = {
            "question_type": "Question Type",
            "text_min_length": "Minimum Characters",
            "text_max_length": "Maximum Characters",
            "text_ideal_answer": "Reference Answer (for AI scoring)",
            "video_max_duration_seconds": "Max Video Duration (seconds)",
            "file_allowed_extensions": "Allowed File Extensions",
            "file_max_size_mb": "Max File Size (MB)",
            "points": "Points",
        }
        help_texts = {
            "question_type": "Select the type of response expected from candidates",
            "text_ideal_answer": "Provide a model answer for AI-assisted scoring",
            "file_allowed_extensions": "Comma-separated list (e.g., pdf,doc,py)",
            "points": "Weight of this question in the overall score",
        }

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get("question_type")
        correct = cleaned_data.get("correct_answer")
        option_a = cleaned_data.get("option_a")
        option_b = cleaned_data.get("option_b")
        option_c = cleaned_data.get("option_c")
        option_d = cleaned_data.get("option_d")

        # Validate multiple choice questions
        if question_type == CustomQuestion.TYPE_MULTIPLE_CHOICE:
            if not option_a:
                self.add_error("option_a", "Option A is required for multiple choice")
            if not option_b:
                self.add_error("option_b", "Option B is required for multiple choice")
            if not correct:
                self.add_error("correct_answer", "Correct answer is required for multiple choice")
            elif correct == "C" and not option_c:
                self.add_error("option_c", "Option C is required when it's the correct answer")
            elif correct == "D" and not option_d:
                self.add_error("option_d", "Option D is required when it's the correct answer")

        # Validate text length constraints
        if question_type in (CustomQuestion.TYPE_TEXT_SHORT, CustomQuestion.TYPE_TEXT_LONG):
            min_len = cleaned_data.get("text_min_length", 0)
            max_len = cleaned_data.get("text_max_length", 5000)
            if min_len >= max_len:
                self.add_error("text_max_length", "Max length must be greater than min length")

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
            choices = []
            if question.option_a:
                choices.append(("A", question.option_a))
            if question.option_b:
                choices.append(("B", question.option_b))
            if question.option_c:
                choices.append(("C", question.option_c))
            if question.option_d:
                choices.append(("D", question.option_d))
            self.fields["answer"].choices = choices


class CandidateTextResponseForm(forms.Form):
    """Form for candidates answering text-based questions."""

    text_response = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-textarea candidate-text-response",
            "rows": 6,
            "placeholder": "Type your answer here...",
        }),
        label="",
    )

    def __init__(self, *args, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        if question:
            self.question = question
            self.fields["text_response"].min_length = question.text_min_length
            self.fields["text_response"].max_length = question.text_max_length

            # Adjust rows based on question type
            if question.question_type == CustomQuestion.TYPE_TEXT_LONG:
                self.fields["text_response"].widget.attrs["rows"] = 12
            else:
                self.fields["text_response"].widget.attrs["rows"] = 4

            # Set placeholder
            if question.text_min_length > 0:
                self.fields["text_response"].widget.attrs["placeholder"] = (
                    f"Type your answer here (minimum {question.text_min_length} characters)..."
                )

    def clean_text_response(self):
        text = self.cleaned_data.get("text_response", "")
        if hasattr(self, "question"):
            if len(text) < self.question.text_min_length:
                raise forms.ValidationError(
                    f"Response must be at least {self.question.text_min_length} characters."
                )
            if len(text) > self.question.text_max_length:
                raise forms.ValidationError(
                    f"Response cannot exceed {self.question.text_max_length} characters."
                )
        return text


class CandidateVideoResponseForm(forms.Form):
    """Form for candidates submitting video responses."""

    video_file = forms.FileField(
        widget=forms.FileInput(attrs={
            "class": "form-file-input video-upload",
            "accept": "video/*",
        }),
        label="Upload Video",
        required=False,
    )

    def __init__(self, *args, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        if question:
            self.question = question
            max_duration = question.video_max_duration_seconds
            self.fields["video_file"].help_text = (
                f"Record or upload a video response (max {max_duration} seconds)"
            )

    def clean_video_file(self):
        video = self.cleaned_data.get("video_file")
        if video:
            # Check file size (max 100MB)
            if video.size > 100 * 1024 * 1024:
                raise forms.ValidationError("Video file must be less than 100MB")

            # Check file extension
            allowed = [".mp4", ".webm", ".mov", ".avi"]
            ext = video.name.lower().split(".")[-1]
            if f".{ext}" not in allowed:
                raise forms.ValidationError(
                    f"Invalid video format. Allowed: {', '.join(allowed)}"
                )
        return video


class CandidateFileUploadForm(forms.Form):
    """Form for candidates uploading files."""

    uploaded_file = forms.FileField(
        widget=forms.FileInput(attrs={
            "class": "form-file-input file-upload",
        }),
        label="Upload File",
    )

    def __init__(self, *args, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        if question:
            self.question = question
            allowed_exts = question.get_allowed_extensions_list()
            self.fields["uploaded_file"].widget.attrs["accept"] = ",".join(
                [f".{ext}" for ext in allowed_exts]
            )
            self.fields["uploaded_file"].help_text = (
                f"Allowed formats: {', '.join(allowed_exts)} | "
                f"Max size: {question.file_max_size_mb}MB"
            )

    def clean_uploaded_file(self):
        f = self.cleaned_data.get("uploaded_file")
        if f and hasattr(self, "question"):
            # Check file size
            max_size = self.question.file_max_size_mb * 1024 * 1024
            if f.size > max_size:
                raise forms.ValidationError(
                    f"File must be less than {self.question.file_max_size_mb}MB"
                )

            # Check file extension
            ext = f.name.lower().split(".")[-1]
            allowed = self.question.get_allowed_extensions_list()
            if ext not in allowed:
                raise forms.ValidationError(
                    f"Invalid file type. Allowed: {', '.join(allowed)}"
                )
        return f


class ManualScoringForm(forms.ModelForm):
    """Form for manually scoring candidate responses."""

    class Meta:
        model = CandidateResponse
        fields = ["score", "score_feedback"]
        widgets = {
            "score": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 0,
                "max": 100,
                "placeholder": "0-100",
            }),
            "score_feedback": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Provide feedback for this response...",
            }),
        }
        labels = {
            "score": "Score (0-100)",
            "score_feedback": "Feedback",
        }

    def clean_score(self):
        score = self.cleaned_data.get("score")
        if score is not None and (score < 0 or score > 100):
            raise forms.ValidationError("Score must be between 0 and 100.")
        return score


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
                client=client_account
            ).order_by("title")
            choices = [("", "— No Project —")]
            choices.extend([(str(p.pk), p.title) for p in projects])
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
