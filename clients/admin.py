from django.contrib import admin
from django.contrib import messages

from .models import ClientAccount
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
    readonly_fields = ("created_at", "updated_at", "email_verified_at", "verification_sent_at")

    fieldsets = (
        ("Account Information", {
            "fields": ("user", "full_name", "company_name", "email", "phone_number", "employee_size")
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
            "fields": ("logo", "logo_data", "logo_mime"),
            "classes": ("collapse",)
        }),
        ("Notes & Settings", {
            "fields": ("notes", "receive_weekly_summary", "data_retention_days")
        }),
        ("Onboarding", {
            "fields": ("has_completed_onboarding", "onboarding_completed_at", "onboarding_step_data"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
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
