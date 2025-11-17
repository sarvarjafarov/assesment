from django.contrib import admin

from .models import ClientAccount


@admin.register(ClientAccount)
class ClientAccountAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "email",
        "status",
        "requested_assessments_display",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("company_name", "email")
    readonly_fields = ("created_at", "updated_at")

    def requested_assessments_display(self, obj: ClientAccount):
        labels = obj.requested_labels()
        return ", ".join(labels) if labels else "—"

    requested_assessments_display.short_description = "Requested assessments"
