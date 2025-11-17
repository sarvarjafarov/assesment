from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ClientAccountQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status="approved")


class ClientAccount(TimeStampedModel):
    EMPLOYEE_SIZE_CHOICES = [
        ("1-10", "1-10"),
        ("11-50", "11-50"),
        ("51-200", "51-200"),
        ("201-500", "201-500"),
        ("500+", "500+"),
    ]
    ASSESSMENT_CHOICES = [
        ("marketing", "Marketing Assessment"),
        ("product", "Product Management Assessment"),
        ("behavioral", "Behavioral Assessment"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        User, related_name="client_account", on_delete=models.CASCADE, null=True, blank=True
    )
    full_name = models.CharField(max_length=120)
    company_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=32)
    employee_size = models.CharField(max_length=16, choices=EMPLOYEE_SIZE_CHOICES)
    requested_assessment = models.CharField(max_length=32, choices=ASSESSMENT_CHOICES)
    allowed_assessments = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True)

    objects = ClientAccountQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.company_name} ({self.email})"

    def has_access(self, assessment_code: str) -> bool:
        return assessment_code in (self.allowed_assessments or [])

    @property
    def approved_assessments(self) -> list[str]:
        return self.allowed_assessments or []
