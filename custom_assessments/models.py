from __future__ import annotations

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
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

    assessment = models.ForeignKey(
        CustomAssessment, on_delete=models.CASCADE, related_name="questions"
    )
    order = models.PositiveIntegerField(default=0)

    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    correct_answer = models.CharField(
        max_length=1,
        help_text="A, B, C, or D",
    )
    explanation = models.TextField(blank=True)

    difficulty_level = models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    category = models.CharField(max_length=100, blank=True)

    ai_generated = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"

    def get_options(self):
        """Return list of (letter, text) tuples for valid options."""
        options = [("A", self.option_a), ("B", self.option_b)]
        if self.option_c:
            options.append(("C", self.option_c))
        if self.option_d:
            options.append(("D", self.option_d))
        return options

    def is_correct(self, answer):
        """Check if the given answer is correct."""
        return answer.upper() == self.correct_answer.upper()


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
        """Calculate the score based on answers."""
        questions = self.assessment.questions.all()
        if not questions:
            self.score = 0
            self.passed = False
            return

        correct = 0
        total = questions.count()

        for question in questions:
            answer = self.answers.get(str(question.pk))
            if answer and question.is_correct(answer):
                correct += 1

        self.score = round((correct / total) * 100, 2) if total > 0 else 0
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
