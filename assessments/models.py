import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Base class to track creation and modification times."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class RoleCategory(TimeStampedModel):
    """High-level grouping for assessments such as Digital Marketing or HR."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True)
    icon = models.CharField(
        max_length=64,
        blank=True,
        help_text="Optional icon token for the front-end (e.g. heroicons-briefcase).",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Assessment(TimeStampedModel):
    """Individual assessment for a role category."""

    LEVEL_CHOICES = [
        ("intro", "Introductory"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    category = models.ForeignKey(
        RoleCategory, related_name="assessments", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    summary = models.TextField()
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="intro",
    )
    duration_minutes = models.PositiveIntegerField(default=20)
    skills_focus = models.JSONField(
        default=list,
        blank=True,
        help_text="List of core skill areas evaluated (stored as strings).",
    )
    scoring_rubric = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional JSON payload describing scoring methodology.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return f"{self.title} ({self.category.name})"


class Question(TimeStampedModel):
    """Represents a single question within an assessment."""

    TYPE_SINGLE = "single"
    TYPE_MULTI = "multi"
    TYPE_SCALE = "scale"
    TYPE_TEXT = "text"
    QUESTION_TYPES = [
        (TYPE_SINGLE, "Single Select"),
        (TYPE_MULTI, "Multi Select"),
        (TYPE_SCALE, "Likert Scale"),
        (TYPE_TEXT, "Free Text"),
    ]

    assessment = models.ForeignKey(
        Assessment, related_name="questions", on_delete=models.CASCADE
    )
    prompt = models.TextField()
    question_type = models.CharField(
        max_length=12, choices=QUESTION_TYPES, default=TYPE_SINGLE
    )
    order = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Use for extra configuration such as scale labels.",
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        help_text="Relative weight when computing a score.",
    )

    class Meta:
        ordering = ("assessment", "order")
        unique_together = ("assessment", "order")

    def __str__(self):
        return f"{self.assessment.title} · Q{self.order}"


class Choice(TimeStampedModel):
    """Possible answer for questions that require options."""

    question = models.ForeignKey(
        Question, related_name="choices", on_delete=models.CASCADE
    )
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=100, blank=True)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        help_text="Contribution to scoring when this choice is selected.",
    )

    class Meta:
        ordering = ("question", "id")

    def __str__(self):
        return self.label


class CandidateProfile(TimeStampedModel):
    """Represents an individual candidate that can receive invitations."""

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True)
    email = models.EmailField(unique=True)
    headline = models.CharField(max_length=180, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("first_name", "last_name")

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class AssessmentSession(TimeStampedModel):
    """Invitation or attempt for a candidate completing an assessment."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("invited", "Invited"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("expired", "Expired"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    candidate = models.ForeignKey(
        CandidateProfile, related_name="sessions", on_delete=models.CASCADE
    )
    assessment = models.ForeignKey(
        Assessment, related_name="sessions", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    invited_by = models.CharField(
        max_length=120,
        blank=True,
        help_text="Internal hiring manager or recruiter creating the invite.",
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    overall_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    score_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Store per-skill statistics and confidence intervals.",
    )
    notes = models.TextField(blank=True)
    due_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional deadline communicated to the candidate.",
    )
    DECISION_CHOICES = [
        ("undecided", "Undecided"),
        ("advance", "Advance"),
        ("reject", "Reject"),
        ("hired", "Hired"),
    ]
    decision = models.CharField(
        max_length=20, choices=DECISION_CHOICES, default="undecided"
    )
    decision_notes = models.TextField(
        blank=True, help_text="Internal notes regarding the decision."
    )

    class Meta:
        unique_together = ("candidate", "assessment")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.candidate} · {self.assessment.title}"


class Response(TimeStampedModel):
    """A candidate's answer for a specific question."""

    session = models.ForeignKey(
        AssessmentSession, related_name="responses", on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question, related_name="responses", on_delete=models.CASCADE
    )
    answer_text = models.TextField(blank=True)
    selected_choices = models.ManyToManyField(
        Choice,
        related_name="responses",
        blank=True,
    )
    score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("session", "question")
        ordering = ("question__order",)

    def __str__(self):
        return f"Response · {self.session} · {self.question}"
