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
    email_host = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMTP host provided by your email provider (e.g., smtp-relay.brevo.com).",
    )
    email_port = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="SMTP port, usually 587 for TLS.",
    )
    email_username = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMTP login/username.",
    )
    email_password = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMTP password or API key.",
    )
    email_use_tls = models.BooleanField(default=True)
    default_from_email = models.CharField(
        max_length=255,
        blank=True,
        help_text="Default From header for transactional messages.",
    )
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
        uploaded_file = getattr(field, "_file", None)
        if uploaded_file is None:
            # No new upload; keep existing binary data untouched.
            return
        uploaded_file.seek(0)
        data = uploaded_file.read()
        if not data:
            return
        mime_type = mimetypes.guess_type(getattr(uploaded_file, "name", ""))[0] or "image/png"
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

    def has_smtp_credentials(self):
        return all(
            [
                self.email_host.strip(),
                self.email_port,
                self.email_username.strip(),
                self.email_password.strip(),
                self.default_from_email.strip(),
            ]
        )

    def smtp_config(self):
        if not self.has_smtp_credentials():
            return {}
        return {
            "EMAIL_HOST": self.email_host.strip(),
            "EMAIL_PORT": self.email_port,
            "EMAIL_HOST_USER": self.email_username.strip(),
            "EMAIL_HOST_PASSWORD": self.email_password.strip(),
            "EMAIL_USE_TLS": self.email_use_tls,
            "DEFAULT_FROM_EMAIL": self.default_from_email.strip(),
        }


class MarketingEmailSettings(MarketingSettings):
    class Meta:
        proxy = True
        verbose_name = "Email Settings"
        verbose_name_plural = "Email Settings"
