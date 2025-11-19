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

    def with_metrics(self):
        return self.annotate(
            total_sessions=models.Count(
                "marketing_sessions", distinct=True
            )
        )


class ClientAccount(TimeStampedModel):
    EMPLOYEE_SIZE_CHOICES = [
        ("1-10", "1-10"),
        ("11-50", "11-50"),
        ("51-200", "51-200"),
        ("201-500", "201-500"),
        ("500+", "500+"),
    ]
    ASSESSMENT_DETAILS = {
        "marketing": {
            "label": "Marketing Assessment",
            "description": "Paid media, SEO, and analytics scenarios to vet growth hires.",
        },
        "product": {
            "label": "Product Management Assessment",
            "description": "Strategy, execution, and product sense cases for PM candidates.",
        },
        "behavioral": {
            "label": "Behavioral Assessment",
            "description": "Psychometric-backed signals covering teamwork and leadership.",
        },
    }
    ASSESSMENT_CHOICES = [
        (code, meta["label"]) for code, meta in ASSESSMENT_DETAILS.items()
    ]
    STATUS_CHOICES = [
        ("pending", "Pending approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("recruiter", "Recruiter"),
        ("interviewer", "Interviewer"),
        ("executive", "Executive"),
        ("viewer", "Viewer"),
    ]

    user = models.OneToOneField(
        User, related_name="client_account", on_delete=models.CASCADE, null=True, blank=True
    )
    full_name = models.CharField(max_length=120)
    company_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=32)
    employee_size = models.CharField(max_length=16, choices=EMPLOYEE_SIZE_CHOICES)
    requested_assessments = models.JSONField(default=list, blank=True)
    allowed_assessments = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="manager")
    notes = models.TextField(blank=True)
    receive_weekly_summary = models.BooleanField(default=False)
    logo = models.FileField(upload_to="client_logos/", null=True, blank=True)

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

    def requested_labels(self) -> list[str]:
        catalog = self.ASSESSMENT_DETAILS
        return [catalog.get(code, {}).get("label", code.title()) for code in self.requested_assessments or []]

    def save(self, *args, **kwargs):
        # Auto-sync the linked user's active flag with client approval status.
        should_activate = self.status == "approved"
        if self.user and self.user.is_active != should_activate:
            self.user.is_active = should_activate
            self.user.save(update_fields=["is_active"])
        super().save(*args, **kwargs)


class ClientNotification(TimeStampedModel):
    LEVEL_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("success", "Success"),
    ]

    client = models.ForeignKey(ClientAccount, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES, default="info")
    link_url = models.URLField(blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.client.company_name}: {self.title}"


class ClientSessionNote(TimeStampedModel):
    ASSESSMENT_CHOICES = ClientAccount.ASSESSMENT_CHOICES
    NOTE_TYPES = [
        ("comment", "Comment"),
        ("decision", "Decision"),
    ]
    DECISION_CHOICES = [
        ("advance", "Advance"),
        ("hold", "Hold"),
        ("reject", "Reject"),
    ]

    client = models.ForeignKey(ClientAccount, related_name="session_notes", on_delete=models.CASCADE)
    assessment_type = models.CharField(max_length=32, choices=ASSESSMENT_CHOICES)
    session_uuid = models.UUIDField()
    candidate_id = models.CharField(max_length=120)
    note = models.TextField(blank=True)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default="comment")
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, blank=True)
    needs_review = models.BooleanField(default=False)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    author_role = models.CharField(max_length=20, choices=ClientAccount.ROLE_CHOICES, default="manager")

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        status = "Needs review" if self.needs_review else self.get_note_type_display()
        return f"{status} for {self.candidate_id}"
