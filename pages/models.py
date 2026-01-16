from django.db import models
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
