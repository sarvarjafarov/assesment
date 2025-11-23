from django.core.cache import cache
from django.db import models

MARKETING_SETTINGS_CACHE_KEY = "marketing_settings_cache"


class MarketingSettings(models.Model):
    site_name = models.CharField(
        max_length=150,
        default="Evalon",
        help_text="Used as a default prefix/suffix for titles across the site.",
    )
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Default title tag when a page does not override it.",
    )
    meta_description = models.TextField(
        blank=True,
        help_text="Default meta description for search and preview cards.",
    )
    meta_keywords = models.CharField(
        max_length=512,
        blank=True,
        help_text="Optional comma-separated keywords for SEO metadata.",
    )
    meta_image = models.FileField(
        upload_to="marketing/meta/",
        blank=True,
        null=True,
        help_text="Used for Open Graph/Twitter preview cards.",
    )
    favicon = models.FileField(
        upload_to="marketing/favicon/",
        blank=True,
        null=True,
        help_text="Small icon that appears in browser tabs.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Marketing & SEO Settings"

    def __str__(self):
        return "Marketing Settings"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(MARKETING_SETTINGS_CACHE_KEY)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete(MARKETING_SETTINGS_CACHE_KEY)
