from __future__ import annotations

import base64
import mimetypes
import secrets
from datetime import datetime
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

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
        "ux_design": {
            "label": "UX/UI Design Assessment",
            "description": "User research, interaction design, visual design, and accessibility scenarios for design hires.",
        },
        "hr": {
            "label": "HR Assessment",
            "description": "Talent acquisition, employee relations, compliance, and people strategy scenarios for HR hires.",
        },
        "finance": {
            "label": "Finance Manager Assessment",
            "description": "Financial planning, budgeting, risk management, and strategic finance scenarios for finance hires.",
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
    AUTH_PROVIDER_CHOICES = [
        ("email", "Email"),
        ("google", "Google"),
        ("linkedin", "LinkedIn"),
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
    auth_provider = models.CharField(
        max_length=20, choices=AUTH_PROVIDER_CHOICES, default="email"
    )
    notes = models.TextField(blank=True)
    receive_weekly_summary = models.BooleanField(default=False)
    receive_completion_alerts = models.BooleanField(
        default=True,
        help_text="Get notified when a candidate completes an assessment"
    )
    receive_new_candidate_alerts = models.BooleanField(
        default=False,
        help_text="Get notified when a new candidate starts an assessment"
    )
    logo = models.FileField(upload_to="client_logos/", null=True, blank=True)
    logo_data = models.BinaryField(blank=True, null=True, editable=False)
    logo_mime = models.CharField(max_length=100, blank=True, editable=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    verification_token = models.CharField(max_length=64, blank=True)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    data_retention_days = models.PositiveIntegerField(default=365)
    plan_slug = models.CharField(max_length=32, choices=PLAN_CHOICES, default="starter")
    invite_quota = models.PositiveIntegerField(default=20)
    project_quota = models.PositiveIntegerField(default=2)
    invite_quota_reset = models.DateField(null=True, blank=True)

    # Onboarding tracking
    has_completed_onboarding = models.BooleanField(default=False)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    onboarding_step_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tracks which steps user has completed: {step_1: true, step_2: false, ...}"
    )

    # Webhook / API Integration
    webhook_url = models.URLField(
        blank=True,
        help_text="URL to receive webhook notifications"
    )
    webhook_secret = models.CharField(
        max_length=64,
        blank=True,
        help_text="Secret key for signing webhook payloads"
    )
    webhook_enabled = models.BooleanField(
        default=False,
        help_text="Enable webhook notifications"
    )
    webhook_events = models.JSONField(
        default=list,
        blank=True,
        help_text="List of event types to trigger webhooks: ['session.created', 'session.started', 'session.completed']"
    )
    api_key = models.CharField(
        max_length=64,
        blank=True,
        help_text="API key for programmatic access"
    )
    api_key_created_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the API key was generated"
    )

    # White-labeling / Branding settings
    brand_primary_color = models.CharField(
        max_length=7,
        default="#ff8a00",
        help_text="Primary brand color (hex code, e.g., #ff8a00)"
    )
    brand_secondary_color = models.CharField(
        max_length=7,
        default="#0e1428",
        help_text="Secondary/text color (hex code)"
    )
    brand_background_color = models.CharField(
        max_length=7,
        default="#ffffff",
        help_text="Background color (hex code)"
    )
    custom_email_sender_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom sender name for assessment emails (e.g., 'Acme Hiring Team')"
    )
    custom_welcome_message = models.TextField(
        blank=True,
        help_text="Custom welcome message shown to candidates on assessment intro page"
    )
    custom_footer_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Custom footer text (replaces 'Powered by Evalon')"
    )
    hide_evalon_branding = models.BooleanField(
        default=False,
        help_text="Hide 'Powered by Evalon' badge (Pro/Enterprise only)"
    )

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

    def generate_verification_token(self) -> str:
        token = secrets.token_urlsafe(32)
        self.verification_token = token
        self.verification_sent_at = timezone.now()
        self.save(update_fields=["verification_token", "verification_sent_at"])
        return token

    def mark_email_verified(self):
        self.email_verified_at = timezone.now()
        self.verification_token = ""
        self.save(update_fields=["email_verified_at", "verification_token"])

    def is_verification_token_valid(self) -> bool:
        """Check if the verification token is still within the 48-hour expiry window."""
        if not self.verification_token or not self.verification_sent_at:
            return False
        from datetime import timedelta
        return timezone.now() - self.verification_sent_at < timedelta(hours=48)

    @property
    def is_email_verified(self) -> bool:
        return bool(self.email_verified_at)

    def mark_onboarding_complete(self):
        """Mark onboarding as completed."""
        self.has_completed_onboarding = True
        self.onboarding_completed_at = timezone.now()
        self.save(update_fields=["has_completed_onboarding", "onboarding_completed_at"])

    def reset_onboarding(self):
        """Allow user to restart onboarding tour."""
        self.has_completed_onboarding = False
        self.onboarding_completed_at = None
        self.onboarding_step_data = {}
        self.save(update_fields=["has_completed_onboarding", "onboarding_completed_at", "onboarding_step_data"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_plan_slug = self.plan_slug

    def save(self, *args, **kwargs):
        self._apply_plan_defaults()
        self._process_logo_upload()
        # Auto-sync the linked user's active flag with client approval status.
        # Social auth users stay active to complete their profile and see pending approval page.
        # Email auth users are activated only after admin approval.
        if self.auth_provider in ('google', 'linkedin'):
            # Social auth users should always be active (they verified email via provider)
            should_activate = True
        else:
            # Email auth users: only active when approved
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

    def _process_logo_upload(self):
        field = getattr(self, "logo")
        if not field:
            return
        uploaded = getattr(field, "_file", None)
        if not uploaded:
            return
        uploaded.seek(0)
        data = uploaded.read()
        if not data:
            return
        mime_type = mimetypes.guess_type(getattr(uploaded, "name", ""))[0] or "image/png"
        self.logo_data = data
        self.logo_mime = mime_type
        field.delete(save=False)
        self.logo = None

    # Plan helpers
    def plan_details(self):
        return self.PLAN_CONFIG.get(self.plan_slug, self.PLAN_CONFIG["starter"])

    def clear_logo(self):
        if self.logo:
            self.logo.delete(save=False)
        self.logo = None
        self.logo_data = None
        self.logo_mime = ""

    @property
    def logo_data_url(self):
        if self.logo_data and self.logo_mime:
            encoded = base64.b64encode(self.logo_data).decode("ascii")
            return f"data:{self.logo_mime};base64,{encoded}"
        if self.logo:
            try:
                return self.logo.url
            except ValueError:
                return None
        return None

    @property
    def has_logo(self):
        return bool(self.logo_data_url)

    @property
    def can_use_white_labeling(self) -> bool:
        """Check if the client's plan supports white-labeling features."""
        return self.plan_slug in ("pro", "enterprise")

    @property
    def can_use_ai_hiring(self) -> bool:
        """Check if the client's plan supports AI hiring pipelines."""
        return self.plan_slug == "enterprise"

    @property
    def branding_css_vars(self) -> dict:
        """Return CSS custom properties for client branding."""
        return {
            "--brand-primary": self.brand_primary_color or "#ff8a00",
            "--brand-secondary": self.brand_secondary_color or "#0e1428",
            "--brand-background": self.brand_background_color or "#ffffff",
        }

    def get_email_sender_name(self) -> str:
        """Return the sender name for emails."""
        if self.custom_email_sender_name and self.can_use_white_labeling:
            return self.custom_email_sender_name
        return f"{self.company_name} via Evalon"

    def get_footer_text(self) -> str:
        """Return the footer text for candidate-facing pages."""
        if self.hide_evalon_branding and self.can_use_white_labeling:
            return self.custom_footer_text or f"Assessment by {self.company_name}"
        return "Powered by Evalon · Secure & confidential"

    def generate_api_key(self) -> str:
        """Generate a new API key for this client."""
        key = f"evl_{uuid.uuid4().hex}"
        self.api_key = key
        self.api_key_created_at = timezone.now()
        self.save(update_fields=["api_key", "api_key_created_at", "updated_at"])
        return key

    def generate_webhook_secret(self) -> str:
        """Generate a new webhook signing secret."""
        secret = f"whsec_{uuid.uuid4().hex}"
        self.webhook_secret = secret
        self.save(update_fields=["webhook_secret", "updated_at"])
        return secret

    def revoke_api_key(self):
        """Revoke the current API key."""
        self.api_key = ""
        self.api_key_created_at = None
        self.save(update_fields=["api_key", "api_key_created_at", "updated_at"])

    @property
    def has_webhook_configured(self) -> bool:
        """Check if webhook is properly configured."""
        return bool(self.webhook_enabled and self.webhook_url and self.webhook_secret)

    def should_trigger_webhook(self, event_type: str) -> bool:
        """Check if a webhook should be triggered for the given event type."""
        if not self.has_webhook_configured:
            return False
        # If no specific events configured, trigger for all
        if not self.webhook_events:
            return True
        return event_type in self.webhook_events

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
        total = 0
        for rel in (
            "marketing_sessions", "pm_sessions", "behavioral_sessions",
            "ux_sessions", "hr_sessions", "finance_sessions",
        ):
            qs = getattr(self, rel, None)
            if qs is not None:
                total += qs.filter(created_at__gte=start_dt).count()
        return total

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
        total = 0
        for rel in (
            "marketing_sessions", "pm_sessions", "behavioral_sessions",
            "ux_sessions", "hr_sessions", "finance_sessions",
        ):
            qs = getattr(self, rel, None)
            if qs is not None:
                total += qs.count()
        return total


class WebhookDelivery(TimeStampedModel):
    """Track webhook delivery attempts and their outcomes."""

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_RETRYING = "retrying"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_RETRYING, "Retrying"),
    ]

    EVENT_SESSION_CREATED = "session.created"
    EVENT_SESSION_STARTED = "session.started"
    EVENT_SESSION_COMPLETED = "session.completed"
    EVENT_SESSION_EXPIRED = "session.expired"
    EVENT_CHOICES = [
        (EVENT_SESSION_CREATED, "Session Created"),
        (EVENT_SESSION_STARTED, "Session Started"),
        (EVENT_SESSION_COMPLETED, "Session Completed"),
        (EVENT_SESSION_EXPIRED, "Session Expired"),
    ]

    client = models.ForeignKey(
        ClientAccount,
        related_name="webhook_deliveries",
        on_delete=models.CASCADE,
    )
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    attempts = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Webhook Delivery"
        verbose_name_plural = "Webhook Deliveries"

    def __str__(self):
        return f"{self.event_type} - {self.client.company_name} ({self.status})"

    def mark_success(self, status_code: int, response_body: str = ""):
        """Mark delivery as successful."""
        self.status = self.STATUS_SUCCESS
        self.response_status_code = status_code
        self.response_body = response_body[:5000]  # Limit response body size
        self.delivered_at = timezone.now()
        self.save(update_fields=[
            "status", "response_status_code", "response_body",
            "delivered_at", "updated_at"
        ])

    def mark_failed(self, status_code: int = None, error: str = ""):
        """Mark delivery as failed."""
        self.attempts += 1
        self.error_message = error[:2000]
        self.response_status_code = status_code

        # Retry logic: retry up to 3 times with exponential backoff
        if self.attempts < 3:
            self.status = self.STATUS_RETRYING
            # 5 minutes, 30 minutes, 2 hours
            delays = [300, 1800, 7200]
            delay = delays[min(self.attempts - 1, len(delays) - 1)]
            self.next_retry_at = timezone.now() + timezone.timedelta(seconds=delay)
        else:
            self.status = self.STATUS_FAILED

        self.save(update_fields=[
            "status", "attempts", "error_message", "response_status_code",
            "next_retry_at", "updated_at"
        ])


class SupportRequest(TimeStampedModel):
    """Track support requests from clients for admin management."""

    TYPE_BILLING = "billing"
    TYPE_TECHNICAL = "technical"
    TYPE_FEATURE = "feature"
    TYPE_OTHER = "other"
    TYPE_CHOICES = [
        (TYPE_BILLING, "Billing & Plans"),
        (TYPE_TECHNICAL, "Technical Issue"),
        (TYPE_FEATURE, "Feature Request"),
        (TYPE_OTHER, "Other"),
    ]

    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CLOSED, "Closed"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]

    client = models.ForeignKey(
        ClientAccount,
        related_name="support_requests",
        on_delete=models.CASCADE,
    )
    request_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_BILLING,
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_NORMAL,
    )
    admin_notes = models.TextField(blank=True, help_text="Internal notes for support team")
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User,
        related_name="resolved_support_requests",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Support Request"
        verbose_name_plural = "Support Requests"

    def __str__(self):
        return f"#{self.pk} - {self.subject} ({self.client.company_name})"

    def mark_resolved(self, user=None):
        """Mark the request as resolved."""
        self.status = self.STATUS_RESOLVED
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save(update_fields=["status", "resolved_at", "resolved_by", "updated_at"])
