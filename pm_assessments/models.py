from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProductQuestionQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_active=True)


class ProductQuestion(TimeStampedModel):
    TYPE_MULTIPLE = "multiple_choice"
    TYPE_OPEN_ENDED = "open_ended"
    TYPE_PRIORITIZATION = "prioritization"
    TYPE_ESTIMATION = "estimation"
    TYPE_REASONING = "reasoning"
    TYPE_BEHAVIORAL_MOST = "behavioral_most"
    TYPE_BEHAVIORAL_LEAST = "behavioral_least"
    QUESTION_TYPES = [
        (TYPE_MULTIPLE, "Multiple choice"),
        (TYPE_OPEN_ENDED, "Open ended"),
        (TYPE_PRIORITIZATION, "Prioritization"),
        (TYPE_ESTIMATION, "Estimation"),
        (TYPE_REASONING, "Reasoning / open response"),
        (TYPE_BEHAVIORAL_MOST, "Behavioral - most like me"),
        (TYPE_BEHAVIORAL_LEAST, "Behavioral - least like me"),
    ]

    CATEGORY_PRODUCT = "product"
    CATEGORY_EXECUTION = "execution"
    CATEGORY_STRATEGY = "strategy"
    CATEGORY_ANALYTICS = "analytics"
    CATEGORY_TECHNICAL = "technical"
    CATEGORY_DESIGN = "design"
    CATEGORY_BEHAVIORAL = "behavioral"
    CATEGORY_CHOICES = [
        (CATEGORY_PRODUCT, "Product sense"),
        (CATEGORY_EXECUTION, "Execution & delivery"),
        (CATEGORY_STRATEGY, "Strategy"),
        (CATEGORY_ANALYTICS, "Analytics"),
        (CATEGORY_TECHNICAL, "Technical"),
        (CATEGORY_DESIGN, "UX & research"),
        (CATEGORY_BEHAVIORAL, "Behavioral & leadership"),
    ]

    question_text = models.TextField()
    question_type = models.CharField(max_length=32, choices=QUESTION_TYPES)
    difficulty_level = models.PositiveSmallIntegerField(default=3)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.JSONField(blank=True, null=True)
    scoring_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    explanation = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = ProductQuestionQuerySet.as_manager()

    class Meta:
        ordering = ("category", "-created_at")

    def __str__(self) -> str:
        return self.question_text[:80]


class ProductAssessmentSession(TimeStampedModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_progress", "In progress"),
        ("paused", "Paused"),
        ("submitted", "Submitted"),
    ]
    client = models.ForeignKey(
        "clients.ClientAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pm_sessions",
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    candidate_id = models.CharField(max_length=120, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    question_set = models.JSONField(default=list)
    responses = models.JSONField(default=list, blank=True)
    hard_skill_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    soft_skill_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    overall_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    category_breakdown = models.JSONField(default=dict, blank=True)
    recommendations = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    last_reminder_at = models.DateTimeField(null=True, blank=True)
    reminder_count = models.PositiveIntegerField(default=0)
    candidate_feedback_score = models.PositiveSmallIntegerField(null=True, blank=True)
    candidate_feedback_comment = models.TextField(blank=True)
    candidate_feedback_submitted_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    total_paused_seconds = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["candidate_id"])]

    def mark_submitted(self):
        self.status = "submitted"
        self.submitted_at = timezone.now()
        self.save(update_fields=["status", "submitted_at"])
