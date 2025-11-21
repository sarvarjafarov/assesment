from django.db import models

from assessments.models import AssessmentSession, TimeStampedModel


class CandidateSupportRequest(TimeStampedModel):
    """On-demand help requests submitted from the candidate experience."""

    TOPIC_CHOICES = [
        ("technical", "Technical issue"),
        ("question", "Question about instructions"),
        ("accessibility", "Accessibility support"),
        ("other", "Something else"),
    ]
    CONTACT_METHOD_CHOICES = [
        ("email", "Email"),
        ("phone", "Phone"),
        ("chat", "Chat handle"),
    ]

    session = models.ForeignKey(
        AssessmentSession,
        related_name="support_requests",
        on_delete=models.CASCADE,
    )
    topic = models.CharField(max_length=32, choices=TOPIC_CHOICES, default="technical")
    message = models.TextField()
    contact_method = models.CharField(
        max_length=20, choices=CONTACT_METHOD_CHOICES, default="email"
    )
    contact_value = models.CharField(max_length=255, blank=True)
    candidate_name = models.CharField(max_length=160, blank=True)
    candidate_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, default="new")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Support request from {self.candidate_name or self.candidate_email or 'candidate'}"
