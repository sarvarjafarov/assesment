import base64
import mimetypes

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
        help_text="Upload an image used for Open Graph/Twitter preview cards.",
    )
    meta_image_data = models.BinaryField(blank=True, null=True, editable=False)
    meta_image_mime = models.CharField(max_length=100, blank=True, editable=False)
    favicon = models.FileField(
        upload_to="marketing/favicon/",
        blank=True,
        null=True,
        help_text="Upload the icon that appears in browser tabs.",
    )
    favicon_data = models.BinaryField(blank=True, null=True, editable=False)
    favicon_mime = models.CharField(max_length=100, blank=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Marketing & SEO Settings"

    def __str__(self):
        return "Marketing Settings"

    def _process_upload(self, field_name):
        field = getattr(self, field_name)
        storage_field = f"{field_name}_data"
        mime_field = f"{field_name}_mime"
        if not field:
            return
        file_obj = getattr(field, "file", None)
        if not file_obj:
            return
        file_obj.open("rb")
        data = file_obj.read()
        file_obj.close()
        if not data:
            return
        mime_type = mimetypes.guess_type(field.name)[0] or "image/png"
        setattr(self, storage_field, data)
        setattr(self, mime_field, mime_type)
        field.delete(save=False)
        setattr(self, field_name, None)

    def save(self, *args, **kwargs):
        self._process_upload("favicon")
        self._process_upload("meta_image")
        super().save(*args, **kwargs)
        cache.delete(MARKETING_SETTINGS_CACHE_KEY)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete(MARKETING_SETTINGS_CACHE_KEY)

    @property
    def favicon_data_url(self):
        if self.favicon_data and self.favicon_mime:
            encoded = base64.b64encode(self.favicon_data).decode("ascii")
            return f"data:{self.favicon_mime};base64,{encoded}"
        return None

    @property
    def has_meta_image(self):
        return bool(self.meta_image_data and self.meta_image_mime)

    def meta_image_response(self):
        if not self.has_meta_image:
            return None, None
        return self.meta_image_data, self.meta_image_mime or "image/png"
