import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone


class DemoRequest(models.Model):
    """Store demo requests from the homepage CTA form."""

    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('scheduled', 'Demo Scheduled'),
        ('completed', 'Demo Completed'),
        ('converted', 'Converted to Customer'),
        ('declined', 'Declined'),
    ]

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    company = models.CharField(max_length=255, blank=True)
    focus_area = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Tracking fields
    contacted_at = models.DateTimeField(null=True, blank=True)
    demo_scheduled_for = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes from the team")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Demo Request'
        verbose_name_plural = 'Demo Requests'

    def __str__(self):
        return f"{self.full_name} ({self.email}) - {self.get_status_display()}"


class APIAccessRequest(models.Model):
    """Store API access requests from the API documentation page."""

    STATUS_CHOICES = [
        ('new', 'New'),
        ('reviewing', 'Under Review'),
        ('approved', 'Approved'),
        ('credentials_sent', 'Credentials Sent'),
        ('active', 'Active Integration'),
        ('declined', 'Declined'),
    ]

    company_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    use_case = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Tracking fields
    reviewed_at = models.DateTimeField(null=True, blank=True)
    api_key_issued_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes from the team")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'API Access Request'
        verbose_name_plural = 'API Access Requests'

    def __str__(self):
        return f"{self.company_name} ({self.contact_email}) - {self.get_status_display()}"


class NewsletterSubscriber(models.Model):
    """Store newsletter subscribers from the footer form."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
    ]

    email = models.EmailField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    subscribed_at = models.DateTimeField(default=timezone.now)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50, default='footer', help_text="Where they subscribed from")

    # For tracking email sends
    last_email_sent_at = models.DateTimeField(null=True, blank=True)
    emails_sent_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'

    def __str__(self):
        return f"{self.email} ({self.get_status_display()})"

    def unsubscribe(self):
        self.status = 'unsubscribed'
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=['status', 'unsubscribed_at'])


class PublicAssessment(models.Model):
    """Public-facing assessment pages for marketing."""

    DIFFICULTY_CHOICES = [
        ('adaptive', 'Adaptive'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    # Core identification
    slug = models.SlugField(unique=True, help_text="URL slug (e.g., 'marketing' for /assessments/marketing/)")
    internal_code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Maps to ClientAccount.allowed_assessments (e.g., 'marketing')"
    )

    # Display content
    title = models.CharField(max_length=160, help_text="Main headline (e.g., 'Marketing IQ Assessment')")
    subtitle = models.CharField(max_length=220, blank=True, help_text="Secondary headline")
    label = models.CharField(max_length=60, help_text="Short label (e.g., 'Marketing IQ')")
    summary = models.TextField(help_text="Brief description for cards and previews")
    description = models.TextField(blank=True, help_text="Extended description for detail page")

    # Visual elements
    icon_svg = models.TextField(blank=True, help_text="SVG code for the assessment icon")
    featured_image = models.URLField(blank=True, help_text="Hero image URL for detail page")

    # Assessment details
    duration_minutes = models.PositiveIntegerField(default=30, help_text="Estimated completion time")
    question_count = models.PositiveIntegerField(default=20, help_text="Number of questions")
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='adaptive',
        help_text="Difficulty level indicator"
    )

    # Structured content (stored as JSON)
    skills_tested = models.JSONField(
        default=list,
        blank=True,
        help_text="List of skills: [{'name': '...', 'description': '...'}]"
    )
    focus_areas = models.JSONField(
        default=list,
        blank=True,
        help_text="List of focus areas: ['Paid media', 'SEO', ...]"
    )
    sample_questions = models.JSONField(
        default=list,
        blank=True,
        help_text="Sample questions: [{'question': '...', 'type': '...'}]"
    )
    stats = models.JSONField(
        default=list,
        blank=True,
        help_text="Display stats: [{'label': '...', 'value': '...'}]"
    )
    use_cases = models.JSONField(
        default=list,
        blank=True,
        help_text="Use cases: [{'title': '...', 'description': '...'}]"
    )
    faqs = models.JSONField(
        default=list,
        blank=True,
        help_text="FAQs: [{'question': '...', 'answer': '...'}]"
    )

    # Rich content
    scoring_rubric = models.TextField(blank=True, help_text="Scoring methodology explanation")
    overview_content = models.TextField(blank=True, help_text="Full overview content (supports HTML)")

    # CTA configuration
    cta_label = models.CharField(max_length=60, default="Start Free Trial")
    cta_url = models.CharField(max_length=200, blank=True, help_text="Custom CTA URL (defaults to demo request)")

    # Display settings
    is_active = models.BooleanField(default=True, help_text="Show on public pages")
    is_featured = models.BooleanField(default=False, help_text="Show on homepage")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower = first)")

    # SEO fields
    meta_title = models.CharField(max_length=160, blank=True, help_text="SEO title (defaults to title)")
    meta_description = models.CharField(max_length=300, blank=True, help_text="SEO description (defaults to summary)")
    meta_keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords")
    meta_image = models.URLField(blank=True, help_text="Social sharing image URL")

    # Preview
    preview_key = models.UUIDField(default=uuid.uuid4, help_text="Secret key for preview access")

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Public Assessment'
        verbose_name_plural = 'Public Assessments'

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse('pages:assessment_detail', kwargs={'slug': self.slug})

    @property
    def focus_list(self):
        """Return focus_areas as a list for template iteration."""
        if isinstance(self.focus_areas, list):
            return self.focus_areas[:4]  # Limit to 4 for display
        return []

    @property
    def seo_title(self):
        return self.meta_title or f"{self.title} | Evalon"

    @property
    def seo_description(self):
        return self.meta_description or self.summary
