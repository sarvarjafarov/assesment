from django.contrib import admin

from .models import MarketingSettings


@admin.register(MarketingSettings)
class MarketingSettingsAdmin(admin.ModelAdmin):
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
