from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SortableModel(TimestampedModel):
    order = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        abstract = True
        ordering = ("order", "id")


class MarketingCopy(TimestampedModel):
    hero_badge = models.CharField(
        max_length=120, default="Backed by Y Combinator", blank=True
    )
    hero_heading = models.CharField(
        max_length=255,
        default="Run assessments and hiring decisions from one console",
        blank=True,
    )
    hero_subheading = models.TextField(
        default="Sira unifies company workflows and the candidate experience—invite talent, capture evidence, auto score, and advance top performers in minutes.",
        blank=True,
    )
    hero_primary_cta = models.CharField(max_length=120, default="Book a Demo", blank=True)
    hero_secondary_cta = models.CharField(
        max_length=120, default="See how it works", blank=True
    )
    cta_title = models.CharField(max_length=255, default="Get started today.", blank=True)
    cta_body = models.TextField(
        default="Full-service support for talent teams rolling out assessments across the org.",
        blank=True,
    )

    def __str__(self) -> str:
        return "Marketing Copy"

    @classmethod
    def current(cls) -> "MarketingCopy":
        instance = cls.objects.first()
        if instance:
            return instance
        return cls()


class Feature(SortableModel):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    panel_title = models.CharField(max_length=255)
    panel_subtitle = models.TextField()
    panel_points = models.TextField(
        help_text="Enter one bullet per line. They will display on the right panel."
    )

    def __str__(self) -> str:
        return self.title

    @property
    def panel_points_list(self) -> list[str]:
        return [item.strip() for item in self.panel_points.splitlines() if item.strip()]


class Article(SortableModel):
    pill_label = models.CharField(max_length=120)
    pill_class = models.CharField(
        max_length=32,
        choices=[
            ("accent", "Accent"),
            ("success", "Success"),
            ("neutral", "Neutral"),
        ],
        default="accent",
    )
    title = models.CharField(max_length=255)
    summary = models.TextField()
    author = models.CharField(max_length=255)
    publish_date = models.DateField()

    def __str__(self) -> str:
        return self.title

    @property
    def date_display(self) -> str:
        return self.publish_date.strftime("%B %d, %Y")


class Testimonial(SortableModel):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    quote = models.TextField()
    avatar_url = models.URLField(blank=True)

    def __str__(self) -> str:
        return self.name
