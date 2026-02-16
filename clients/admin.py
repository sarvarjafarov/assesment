from django.contrib import admin
from django.contrib import messages
from django.utils import timezone

from .models import ClientAccount, PositionApplication, SupportRequest
from .services import send_welcome_email


@admin.register(ClientAccount)
class ClientAccountAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "email",
        "status",
        "email_verified_at",
        "requested_assessments_display",
        "created_at",
    )
    list_filter = ("status", "plan_slug")
    search_fields = ("company_name", "email", "full_name")
    readonly_fields = (
        "created_at",
        "updated_at",
        "email_verified_at",
        "verification_sent_at",
        "logo_data",  # Binary field, display only
        "logo_mime",  # Display only
    )

    fieldsets = (
        ("Account Information", {
            "fields": ("user", "full_name", "company_name", "slug", "email", "phone_number", "employee_size")
        }),
        ("Status & Verification", {
            "fields": ("status", "email_verified_at", "verification_sent_at")
        }),
        ("Assessments & Access", {
            "fields": ("requested_assessments", "allowed_assessments", "role")
        }),
        ("Plan & Billing", {
            "fields": ("plan_slug", "project_quota", "invite_quota", "invite_quota_reset")
        }),
        ("Branding", {
            "fields": ("logo",),
            "description": "Upload a company logo (PNG, JPG, or SVG, max 2MB). The logo is automatically processed and stored."
        }),
        ("Notes & Settings", {
            "fields": ("notes", "receive_weekly_summary", "data_retention_days")
        }),
        ("Onboarding", {
            "fields": ("has_completed_onboarding", "onboarding_completed_at", "onboarding_step_data"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def requested_assessments_display(self, obj: ClientAccount):
        labels = obj.requested_labels()
        return ", ".join(labels) if labels else "—"

    requested_assessments_display.short_description = "Requested assessments"

    def save_model(self, request, obj, form, change):
        """
        Send welcome email when account is approved.
        """
        # Check if status is changing to approved
        if change and "status" in form.changed_data:
            old_status = form.initial.get("status")
            new_status = obj.status

            # Send welcome email when approving an account
            if old_status != "approved" and new_status == "approved":
                super().save_model(request, obj, form, change)

                # Send welcome email
                email_sent = send_welcome_email(obj)
                if email_sent:
                    messages.success(
                        request,
                        f"Welcome email sent to {obj.email}"
                    )
                else:
                    messages.warning(
                        request,
                        f"Account approved but failed to send welcome email to {obj.email}"
                    )
                return

        super().save_model(request, obj, form, change)


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "client_company",
        "request_type",
        "status",
        "priority",
        "created_at",
    )
    list_filter = ("status", "request_type", "priority", "created_at")
    search_fields = ("subject", "message", "client__company_name", "client__email")
    readonly_fields = ("created_at", "updated_at", "resolved_at", "resolved_by")
    list_editable = ("status", "priority")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        ("Request Details", {
            "fields": ("client", "request_type", "subject", "message")
        }),
        ("Status", {
            "fields": ("status", "priority")
        }),
        ("Admin Response", {
            "fields": ("admin_notes",),
            "classes": ("wide",)
        }),
        ("Resolution", {
            "fields": ("resolved_at", "resolved_by"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    actions = ["mark_resolved", "mark_in_progress", "mark_closed"]

    def client_company(self, obj):
        return obj.client.company_name
    client_company.short_description = "Company"
    client_company.admin_order_field = "client__company_name"

    def mark_resolved(self, request, queryset):
        count = 0
        for obj in queryset:
            if obj.status != SupportRequest.STATUS_RESOLVED:
                obj.status = SupportRequest.STATUS_RESOLVED
                obj.resolved_at = timezone.now()
                obj.resolved_by = request.user
                obj.save(update_fields=["status", "resolved_at", "resolved_by", "updated_at"])
                count += 1
        self.message_user(request, f"{count} request(s) marked as resolved.")
    mark_resolved.short_description = "Mark selected as resolved"

    def mark_in_progress(self, request, queryset):
        count = queryset.update(status=SupportRequest.STATUS_IN_PROGRESS)
        self.message_user(request, f"{count} request(s) marked as in progress.")
    mark_in_progress.short_description = "Mark selected as in progress"

    def mark_closed(self, request, queryset):
        count = queryset.update(status=SupportRequest.STATUS_CLOSED)
        self.message_user(request, f"{count} request(s) marked as closed.")
    mark_closed.short_description = "Mark selected as closed"


@admin.register(PositionApplication)
class PositionApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "project", "assessment_type", "status", "created_at")
    list_filter = ("status", "assessment_type")
    search_fields = ("full_name", "email", "project__title")
    readonly_fields = ("uuid", "resume_data", "ip_address", "created_at", "updated_at")
