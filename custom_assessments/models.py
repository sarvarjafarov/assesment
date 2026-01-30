from __future__ import annotations

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from assessments.constants import PIPELINE_STAGE_CHOICES

from .constants import LEVEL_CHOICES, LEVEL_JUNIOR, LEVEL_MID, LEVEL_SENIOR


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomAssessment(TimeStampedModel):
    """Client-created custom assessment."""

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    client = models.ForeignKey(
        "clients.ClientAccount",
        on_delete=models.CASCADE,
        related_name="custom_assessments",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # AI Generation metadata
    role_description = models.TextField(
        blank=True, help_text="Role this assessment targets"
    )
    skills_to_test = models.TextField(blank=True, help_text="Skills/knowledge areas")
    ai_generated = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    time_limit_minutes = models.PositiveIntegerField(default=30)
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum percentage to pass",
    )

    # Anti-cheating settings
    require_fullscreen = models.BooleanField(
        default=False,
        help_text="Require candidates to use full-screen mode"
    )
    detect_tab_switches = models.BooleanField(
        default=True,
        help_text="Track when candidates switch tabs/windows"
    )
    prevent_copy_paste = models.BooleanField(
        default=True,
        help_text="Prevent copying question text"
    )
    max_tab_switches = models.PositiveIntegerField(
        default=3,
        help_text="Max allowed tab switches before flagging (0 = unlimited)"
    )

    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.client.company_name})"

    def question_count(self):
        return self.questions.count()

    def publish(self):
        """Publish the assessment, making it available for use."""
        if self.questions.count() < 1:
            raise ValueError("Cannot publish assessment with no questions")
        self.status = self.STATUS_PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def archive(self):
        """Archive the assessment."""
        self.status = self.STATUS_ARCHIVED
        self.save(update_fields=["status", "updated_at"])

    @transaction.atomic
    def duplicate(self):
        """Create a copy of this assessment with all questions."""
        new_assessment = CustomAssessment.objects.create(
            client=self.client,
            name=f"{self.name} (Copy)",
            description=self.description,
            role_description=self.role_description,
            skills_to_test=self.skills_to_test,
            ai_generated=self.ai_generated,
            time_limit_minutes=self.time_limit_minutes,
            passing_score=self.passing_score,
            status=self.STATUS_DRAFT,
        )
        for question in self.questions.all():
            CustomQuestion.objects.create(
                assessment=new_assessment,
                order=question.order,
                question_text=question.question_text,
                option_a=question.option_a,
                option_b=question.option_b,
                option_c=question.option_c,
                option_d=question.option_d,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                difficulty_level=question.difficulty_level,
                category=question.category,
                ai_generated=question.ai_generated,
            )
        return new_assessment


class CustomQuestion(TimeStampedModel):
    """Question within a custom assessment."""

    # Question types
    TYPE_MULTIPLE_CHOICE = "multiple_choice"
    TYPE_TEXT_SHORT = "text_short"
    TYPE_TEXT_LONG = "text_long"
    TYPE_VIDEO = "video"
    TYPE_FILE_UPLOAD = "file_upload"
    TYPE_CHOICES = [
        (TYPE_MULTIPLE_CHOICE, "Multiple Choice"),
        (TYPE_TEXT_SHORT, "Short Text"),
        (TYPE_TEXT_LONG, "Long Text / Essay"),
        (TYPE_VIDEO, "Video Response"),
        (TYPE_FILE_UPLOAD, "File Upload"),
    ]

    assessment = models.ForeignKey(
        CustomAssessment, on_delete=models.CASCADE, related_name="questions"
    )
    order = models.PositiveIntegerField(default=0)

    # Question type (new field)
    question_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_MULTIPLE_CHOICE,
    )

    question_text = models.TextField()

    # Multiple choice options (only used for multiple_choice type)
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    correct_answer = models.CharField(
        max_length=1,
        blank=True,
        help_text="A, B, C, or D (for multiple choice)",
    )

    # Text question settings
    text_min_length = models.PositiveIntegerField(
        default=0,
        help_text="Minimum character count for text responses"
    )
    text_max_length = models.PositiveIntegerField(
        default=5000,
        help_text="Maximum character count for text responses"
    )
    text_ideal_answer = models.TextField(
        blank=True,
        help_text="Ideal answer for AI scoring reference"
    )

    # Video question settings
    video_max_duration_seconds = models.PositiveIntegerField(
        default=120,
        help_text="Maximum video duration in seconds"
    )

    # File upload settings
    file_allowed_extensions = models.CharField(
        max_length=200,
        blank=True,
        default="pdf,doc,docx,txt,py,js,java,cpp",
        help_text="Comma-separated list of allowed file extensions"
    )
    file_max_size_mb = models.PositiveIntegerField(
        default=10,
        help_text="Maximum file size in MB"
    )

    explanation = models.TextField(blank=True)

    # Scoring
    difficulty_level = models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    points = models.PositiveIntegerField(
        default=1,
        help_text="Points for this question (for weighted scoring)"
    )
    requires_manual_scoring = models.BooleanField(
        default=False,
        help_text="Whether this question requires manual scoring"
    )

    category = models.CharField(max_length=100, blank=True)

    ai_generated = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"

    def get_options(self):
        """Return list of (letter, text) tuples for valid options."""
        if self.question_type != self.TYPE_MULTIPLE_CHOICE:
            return []
        options = []
        if self.option_a:
            options.append(("A", self.option_a))
        if self.option_b:
            options.append(("B", self.option_b))
        if self.option_c:
            options.append(("C", self.option_c))
        if self.option_d:
            options.append(("D", self.option_d))
        return options

    def is_correct(self, answer):
        """Check if the given answer is correct (for multiple choice only)."""
        if self.question_type != self.TYPE_MULTIPLE_CHOICE:
            return None  # Non-MC questions need manual/AI scoring
        if not self.correct_answer or not answer:
            return False
        return answer.upper() == self.correct_answer.upper()

    def is_auto_scoreable(self):
        """Check if this question can be auto-scored."""
        return self.question_type == self.TYPE_MULTIPLE_CHOICE

    def get_allowed_extensions_list(self):
        """Return list of allowed file extensions."""
        if not self.file_allowed_extensions:
            return []
        return [ext.strip().lower() for ext in self.file_allowed_extensions.split(",")]


class CustomAssessmentSession(TimeStampedModel):
    """Candidate session for a custom assessment."""

    STATUS_DRAFT = "draft"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_SUBMITTED = "submitted"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_SUBMITTED, "Submitted"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    assessment = models.ForeignKey(
        CustomAssessment, on_delete=models.CASCADE, related_name="sessions"
    )
    client = models.ForeignKey(
        "clients.ClientAccount",
        on_delete=models.CASCADE,
        related_name="custom_sessions",
    )
    project = models.ForeignKey(
        "clients.ClientProject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="custom_sessions",
    )

    candidate_id = models.CharField(max_length=120, db_index=True)
    candidate_email = models.EmailField(blank=True)

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default=LEVEL_MID)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )

    # Progress tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_question_index = models.PositiveIntegerField(default=0)

    # Results stored as JSON: {question_id: selected_answer}
    answers = models.JSONField(default=dict)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)

    # Question order (shuffled from assessment)
    question_order = models.JSONField(default=list)

    # Pipeline integration
    pipeline_stage = models.CharField(
        max_length=32,
        choices=PIPELINE_STAGE_CHOICES,
        default="invited",
    )
    pipeline_stage_updated_at = models.DateTimeField(null=True, blank=True)

    # Deadline settings
    deadline_at = models.DateTimeField(null=True, blank=True)

    # Anti-cheating telemetry
    telemetry_log = models.JSONField(
        default=list,
        help_text="Activity log for anti-cheating analysis"
    )
    tab_switch_count = models.PositiveIntegerField(default=0)
    copy_attempt_count = models.PositiveIntegerField(default=0)
    fullscreen_exit_count = models.PositiveIntegerField(default=0)
    trust_score = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Trust score based on behavior (100 = fully trusted)"
    )
    flagged_for_review = models.BooleanField(
        default=False,
        help_text="Flagged for manual review due to suspicious activity"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["candidate_id"]),
            models.Index(fields=["assessment", "status"]),
        ]

    def __str__(self):
        return f"{self.candidate_id} - {self.assessment.name}"

    def start(self):
        """Mark session as started."""
        if not self.started_at:
            self.started_at = timezone.now()
            self.status = self.STATUS_IN_PROGRESS
            if self.pipeline_stage == "invited":
                self.pipeline_stage = "in_progress"
                self.pipeline_stage_updated_at = timezone.now()
            self.save(
                update_fields=[
                    "started_at",
                    "status",
                    "pipeline_stage",
                    "pipeline_stage_updated_at",
                    "updated_at",
                ]
            )

    def submit(self):
        """Mark session as submitted and calculate score."""
        self.status = self.STATUS_SUBMITTED
        self.completed_at = timezone.now()
        self.pipeline_stage = "submitted"
        self.pipeline_stage_updated_at = timezone.now()

        # Calculate score
        self._calculate_score()

        self.save(
            update_fields=[
                "status",
                "completed_at",
                "pipeline_stage",
                "pipeline_stage_updated_at",
                "score",
                "passed",
                "updated_at",
            ]
        )

    def _calculate_score(self):
        """
        Calculate the score based on answers.

        For multiple choice: auto-scored based on correct answer
        For text/video/file: uses score from CandidateResponse if available
        """
        questions = self.assessment.questions.all()
        if not questions:
            self.score = 0
            self.passed = False
            return

        total_points = 0
        earned_points = 0
        has_unscored = False

        for question in questions:
            total_points += question.points

            if question.is_auto_scoreable():
                # Multiple choice - auto-score
                answer = self.answers.get(str(question.pk))
                if answer and question.is_correct(answer):
                    earned_points += question.points
            else:
                # Non-MC question - check CandidateResponse for score
                response = self.responses.filter(question=question).first()
                if response and response.score is not None:
                    # Convert 0-100 score to points
                    earned_points += (response.score / 100) * question.points
                else:
                    has_unscored = True

        if total_points > 0:
            self.score = round((earned_points / total_points) * 100, 2)
        else:
            self.score = 0

        # Only mark as passed if all questions are scored
        if has_unscored:
            self.passed = None  # Pending scoring
        else:
            self.passed = self.score >= self.assessment.passing_score

    def get_current_question(self):
        """Get the current question based on progress."""
        if not self.question_order:
            return None
        if self.current_question_index >= len(self.question_order):
            return None
        question_id = self.question_order[self.current_question_index]
        return CustomQuestion.objects.filter(pk=question_id).first()

    def record_answer(self, question_id, answer):
        """Record an answer for a question."""
        self.answers[str(question_id)] = answer.upper()
        self.save(update_fields=["answers", "updated_at"])

    def progress_percentage(self):
        """Return completion percentage."""
        total = len(self.question_order) if self.question_order else 0
        if total == 0:
            return 0
        return int((self.current_question_index / total) * 100)

    def log_telemetry_event(self, event_type: str, details: dict = None):
        """
        Log an anti-cheating telemetry event.

        Event types:
        - tab_switch: Candidate switched tabs/windows
        - copy_attempt: Candidate tried to copy text
        - paste_attempt: Candidate tried to paste text
        - fullscreen_exit: Candidate exited fullscreen mode
        - fullscreen_enter: Candidate entered fullscreen mode
        - right_click: Candidate right-clicked
        - keyboard_shortcut: Suspicious keyboard shortcut detected
        """
        event = {
            "type": event_type,
            "timestamp": timezone.now().isoformat(),
            "question_index": self.current_question_index,
        }
        if details:
            event["details"] = details

        self.telemetry_log.append(event)

        # Update counters and trust score
        trust_penalty = 0
        if event_type == "tab_switch":
            self.tab_switch_count += 1
            trust_penalty = 10
        elif event_type in ("copy_attempt", "paste_attempt"):
            self.copy_attempt_count += 1
            trust_penalty = 5
        elif event_type == "fullscreen_exit":
            self.fullscreen_exit_count += 1
            trust_penalty = 15

        # Apply trust penalty
        if trust_penalty > 0:
            self.trust_score = max(0, self.trust_score - trust_penalty)

        # Flag for review if trust score drops too low or too many violations
        max_switches = self.assessment.max_tab_switches
        if self.trust_score < 50 or (max_switches > 0 and self.tab_switch_count > max_switches):
            self.flagged_for_review = True

        self.save(update_fields=[
            "telemetry_log",
            "tab_switch_count",
            "copy_attempt_count",
            "fullscreen_exit_count",
            "trust_score",
            "flagged_for_review",
            "updated_at",
        ])


def candidate_upload_path(instance, filename):
    """Generate upload path for candidate files/videos."""
    return f"candidate_responses/{instance.session.uuid}/{instance.question.pk}/{filename}"


class CandidateResponse(TimeStampedModel):
    """
    Stores candidate responses for non-multiple-choice questions.
    Multiple choice answers are stored in CustomAssessmentSession.answers JSON field.
    """

    session = models.ForeignKey(
        CustomAssessmentSession,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    question = models.ForeignKey(
        CustomQuestion,
        on_delete=models.CASCADE,
        related_name="candidate_responses",
    )

    # Text responses
    text_response = models.TextField(blank=True)

    # Video responses
    video_file = models.FileField(
        upload_to=candidate_upload_path,
        blank=True,
        null=True,
    )
    video_duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    # File upload responses
    uploaded_file = models.FileField(
        upload_to=candidate_upload_path,
        blank=True,
        null=True,
    )
    uploaded_file_name = models.CharField(max_length=255, blank=True)

    # Scoring (for manual/AI grading)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Score out of 100 for this response"
    )
    score_feedback = models.TextField(
        blank=True,
        help_text="Feedback from evaluator or AI"
    )
    scored_by = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("manual", "Manual"),
            ("ai", "AI"),
        ],
        default="pending",
    )
    scored_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["session", "question"]
        ordering = ["question__order"]

    def __str__(self):
        return f"Response: {self.session.candidate_id} - Q{self.question.order}"

    def get_response_display(self):
        """Return a display-friendly version of the response."""
        if self.question.question_type == CustomQuestion.TYPE_TEXT_SHORT:
            return self.text_response[:100] + "..." if len(self.text_response) > 100 else self.text_response
        elif self.question.question_type == CustomQuestion.TYPE_TEXT_LONG:
            return self.text_response[:200] + "..." if len(self.text_response) > 200 else self.text_response
        elif self.question.question_type == CustomQuestion.TYPE_VIDEO:
            return f"Video ({self.video_duration_seconds}s)" if self.video_file else "No video"
        elif self.question.question_type == CustomQuestion.TYPE_FILE_UPLOAD:
            return self.uploaded_file_name or "No file"
        return ""

    def is_scored(self):
        """Check if this response has been scored."""
        return self.score is not None
