from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DigitalMarketingQuestionQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_active=True)


class DigitalMarketingQuestion(TimeStampedModel):
    TYPE_MULTIPLE = "multiple_choice"
    TYPE_SCENARIO = "scenario"
    TYPE_RANKING = "ranking"
    TYPE_BEHAVIORAL_MOST = "behavioral_most"
    TYPE_BEHAVIORAL_LEAST = "behavioral_least"
    TYPE_REASONING = "reasoning"
    QUESTION_TYPES = [
        (TYPE_MULTIPLE, "Multiple choice"),
        (TYPE_SCENARIO, "Scenario based"),
        (TYPE_RANKING, "Ranking / Ordering"),
        (TYPE_BEHAVIORAL_MOST, "Behavioral - most like me"),
        (TYPE_BEHAVIORAL_LEAST, "Behavioral - least like me"),
        (TYPE_REASONING, "Reasoning / open response"),
    ]

    CATEGORY_PPC = "ppc"
    CATEGORY_SEO = "seo"
    CATEGORY_ANALYTICS = "analytics"
    CATEGORY_CONTENT = "content"
    CATEGORY_SOCIAL = "social"
    CATEGORY_STRATEGY = "strategy"
    CATEGORY_BEHAVIORAL = "behavioral"
    CATEGORY_CHOICES = [
        (CATEGORY_PPC, "PPC / Paid Media"),
        (CATEGORY_SEO, "SEO"),
        (CATEGORY_ANALYTICS, "Analytics"),
        (CATEGORY_CONTENT, "Content & Copy"),
        (CATEGORY_SOCIAL, "Social Media"),
        (CATEGORY_STRATEGY, "Strategy & Problem Solving"),
        (CATEGORY_BEHAVIORAL, "Behavioral"),
    ]

    question_text = models.TextField()
    question_type = models.CharField(max_length=32, choices=QUESTION_TYPES)
    difficulty_level = models.PositiveSmallIntegerField(default=3)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    options = models.JSONField(default=dict, blank=True)
    correct_answer = models.JSONField(blank=True, null=True)
    scoring_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    explanation = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = DigitalMarketingQuestionQuerySet.as_manager()

    class Meta:
        ordering = ("category", "-created_at")

    def __str__(self):
        return self.question_text[:80]


class DigitalMarketingAssessmentSession(TimeStampedModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_progress", "In progress"),
        ("submitted", "Submitted"),
    ]
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

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["candidate_id"]),
        ]

    def mark_submitted(self):
        self.status = "submitted"
        self.submitted_at = timezone.now()
