from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from datetime import datetime
import uuid

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
    PLAN_CONFIG = {
        "starter": {
            "label": "Starter",
            "project_quota": 2,
            "invite_quota": 20,
            "description": "Free plan for pilots",
        },
        "pro": {
            "label": "Pro",
            "project_quota": 10,
            "invite_quota": 250,
            "description": "Unlimited reviewers + branding",
        },
        "enterprise": {
            "label": "Enterprise",
            "project_quota": 0,
            "invite_quota": 0,
            "description": "Custom limits and SLAs",
        },
    }
    EMPLOYEE_SIZE_CHOICES = [
        ("1-10", "1-10"),
        ("11-50", "11-50"),
        ("51-200", "51-200"),
        ("201-500", "201-500"),
        ("500+", "500+"),
    ]
    PLAN_CHOICES = [
        ("starter", "Starter"),
        ("pro", "Pro"),
        ("enterprise", "Enterprise"),
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
    data_retention_days = models.PositiveIntegerField(default=365)
    plan_slug = models.CharField(max_length=32, choices=PLAN_CHOICES, default="starter")
    invite_quota = models.PositiveIntegerField(default=20)
    project_quota = models.PositiveIntegerField(default=2)
    invite_quota_reset = models.DateField(null=True, blank=True)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_plan_slug = self.plan_slug

    def save(self, *args, **kwargs):
        self._apply_plan_defaults()
        # Auto-sync the linked user's active flag with client approval status.
        should_activate = self.status == "approved"
        if self.user and self.user.is_active != should_activate:
            self.user.is_active = should_activate
            self.user.save(update_fields=["is_active"])
        super().save(*args, **kwargs)
        self._original_plan_slug = self.plan_slug

    def _apply_plan_defaults(self):
        config = self.PLAN_CONFIG.get(self.plan_slug)
        if not config:
            return
        plan_project = config.get("project_quota")
        plan_invite = config.get("invite_quota")
        if plan_project is not None:
            self.project_quota = plan_project
        if plan_invite is not None:
            self.invite_quota = plan_invite

    # Plan helpers
    def plan_details(self):
        return self.PLAN_CONFIG.get(self.plan_slug, self.PLAN_CONFIG["starter"])

    def project_limit(self) -> int | None:
        limit = self.project_quota
        if limit in (0, None):
            return None
        return limit

    def invite_limit(self) -> int | None:
        limit = self.invite_quota
        if limit in (0, None):
            return None
        return limit

    def active_project_count(self) -> int:
        return self.projects.exclude(status=ClientProject.STATUS_ARCHIVED).count()

    def remaining_projects(self) -> int | None:
        limit = self.project_limit()
        if limit is None:
            return None
        remaining = limit - self.active_project_count()
        return max(remaining, 0)

    def _invite_window_start(self):
        now = timezone.localtime()
        current_month_start = now.replace(day=1).date()
        if not self.invite_quota_reset or self.invite_quota_reset < current_month_start:
            if self.pk:
                type(self).objects.filter(pk=self.pk).update(invite_quota_reset=current_month_start)
            self.invite_quota_reset = current_month_start
        return self.invite_quota_reset

    def invites_used(self) -> int:
        window_start = self._invite_window_start()
        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(window_start, datetime.min.time()), tz)
        return (
            self.marketing_sessions.filter(created_at__gte=start_dt).count()
            + getattr(self, "pm_sessions").filter(created_at__gte=start_dt).count()
            + self.behavioral_sessions.filter(created_at__gte=start_dt).count()
        )

    def invites_remaining(self) -> int | None:
        limit = self.invite_limit()
        if limit is None:
            return None
        remaining = limit - self.invites_used()
        return max(remaining, 0)


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


class ClientProject(TimeStampedModel):
    STATUS_ACTIVE = "active"
    STATUS_ON_HOLD = "on_hold"
    STATUS_FILLED = "filled"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Actively hiring"),
        (STATUS_ON_HOLD, "On hold"),
        (STATUS_FILLED, "Role filled"),
        (STATUS_ARCHIVED, "Archived"),
    ]
    PRIORITY_CHOICES = [
        ("p0", "Critical"),
        ("p1", "High"),
        ("p2", "Medium"),
        ("p3", "Low"),
    ]

    client = models.ForeignKey(ClientAccount, related_name="projects", on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200)
    role_level = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="p1")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    open_roles = models.PositiveIntegerField(default=1)
    target_start_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title} ({self.client.company_name})"

    def total_sessions(self):
        return (
            self.marketing_sessions.count()
            + getattr(self, "pm_sessions").count()
            + self.behavioral_sessions.count()
        )
