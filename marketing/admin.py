from django import forms
from django.contrib import admin

from .models import MarketingEmailSettings, MarketingSettings


class MarketingSettingsAdminForm(forms.ModelForm):
    class Meta:
        model = MarketingSettings
        fields = "__all__"
        widgets = {
            "email_password": forms.PasswordInput(render_value=True),
        }


@admin.register(MarketingSettings)
class MarketingSettingsAdmin(admin.ModelAdmin):
    form = MarketingSettingsAdminForm
    fieldsets = (
        (
            "Branding",
            {
                "fields": (
                    "site_name",
                    "favicon",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "meta_image",
                )
            },
        ),
        (
            "Email delivery",
            {
                "fields": (
                    "default_from_email",
                    "email_host",
                    "email_port",
                    "email_username",
                    "email_password",
                    "email_use_tls",
                )
            },
        ),
        (
            "System",
            {
                "fields": ("updated_at",),
            },
        ),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        if MarketingSettings.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(MarketingEmailSettings)
class MarketingEmailSettingsAdmin(admin.ModelAdmin):
    form = MarketingSettingsAdminForm
    fieldsets = (
        (
            "Email delivery",
            {
                "fields": (
                    "default_from_email",
                    "email_host",
                    "email_port",
                    "email_username",
                    "email_password",
                    "email_use_tls",
                )
            },
        ),
    )
    readonly_fields = ()

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return MarketingEmailSettings.objects.all()
