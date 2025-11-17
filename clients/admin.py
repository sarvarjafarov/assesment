from django.contrib import admin

from .models import ClientAccount


@admin.register(ClientAccount)
class ClientAccountAdmin(admin.ModelAdmin):
    list_display = ("company_name", "email", "status", "requested_assessment", "created_at")
    list_filter = ("status", "requested_assessment")
    search_fields = ("company_name", "email")
    readonly_fields = ("created_at", "updated_at")
