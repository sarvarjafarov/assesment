import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BlogPostQuerySet(models.QuerySet):
    def published(self):
        now = timezone.now()
        return self.filter(status="published", published_at__lte=now)


class BlogPost(TimeStampedModel):
    """Rich, SEO-friendly articles surfaced on the marketing site."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("published", "Published"),
    ]
    PILL_STYLE_CHOICES = [
        ("accent", "Accent"),
        ("success", "Success"),
        ("neutral", "Neutral"),
    ]

    title = models.CharField(max_length=220)
    slug = models.SlugField(unique=True)
    hero_image = models.URLField(blank=True)
    pill_label = models.CharField(max_length=60, default="Insights")
    pill_style = models.CharField(
        max_length=20, choices=PILL_STYLE_CHOICES, default="accent"
    )
    excerpt = models.TextField(
        help_text="Short teaser shown on the homepage and list view."
    )
    body = models.TextField(help_text="Supports Markdown or HTML snippets.")
    author_name = models.CharField(max_length=120)
    author_title = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    published_at = models.DateTimeField(null=True, blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(
        max_length=255, blank=True, help_text="Comma separated keywords."
    )
    meta_image = models.URLField(
        blank=True, help_text="Social preview image (absolute URL)."
    )
    is_featured = models.BooleanField(
        default=False, help_text="Surface in the homepage hero slot."
    )
    preview_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    objects = BlogPostQuerySet.as_manager()

    class Meta:
        ordering = ("-published_at", "-created_at")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:detail", args=[self.slug])

    @property
    def is_published(self) -> bool:
        return (
            self.status == "published"
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )

    def display_author(self):
        if self.author_title:
            return f"{self.author_name}, {self.author_title}"
        return self.author_name

    def estimated_read_minutes(self) -> int:
        """Roughly estimate read time assuming ~200 words per minute."""
        if not self.body:
            return 3
        word_count = len(self.body.split())
        minutes = max(1, round(word_count / 200))
        return max(3, minutes)
