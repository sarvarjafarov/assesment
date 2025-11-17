from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BehavioralQuestionQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_active=True)


class BehavioralQuestion(TimeStampedModel):
    block_id = models.PositiveIntegerField(unique=True)
    prompt = models.CharField(
        max_length=255,
        default="Select the statements that best describe you.",
    )
    statements = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    objects = BehavioralQuestionQuerySet.as_manager()

    class Meta:
        ordering = ("block_id",)

    def __str__(self):
        return f"Behavioral block {self.block_id}"


class BehavioralAssessmentSession(TimeStampedModel):
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
    trait_scores = models.JSONField(default=dict, blank=True)
    profile_report = models.JSONField(default=dict, blank=True)
    eligibility_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    eligibility_label = models.CharField(max_length=64, blank=True)
    risk_flags = models.JSONField(default=list, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=20)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["candidate_id"])]

    def mark_submitted(self):
        self.status = "submitted"
        self.submitted_at = timezone.now()
