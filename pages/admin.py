from django.contrib import admin
from .models import DemoRequest, APIAccessRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'company', 'focus_area', 'status', 'created_at']
    list_filter = ['status', 'focus_area', 'created_at']
    search_fields = ['full_name', 'email', 'company', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'company')
        }),
        ('Request Details', {
            'fields': ('focus_area', 'notes')
        }),
        ('Status & Follow-up', {
            'fields': ('status', 'contacted_at', 'demo_scheduled_for', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_contacted', 'mark_as_scheduled']

    def mark_as_contacted(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='contacted', contacted_at=timezone.now())
        self.message_user(request, f'{updated} demo request(s) marked as contacted.')
    mark_as_contacted.short_description = "Mark selected as Contacted"

    def mark_as_scheduled(self, request, queryset):
        updated = queryset.update(status='scheduled')
        self.message_user(request, f'{updated} demo request(s) marked as Demo Scheduled.')
    mark_as_scheduled.short_description = "Mark selected as Demo Scheduled"


@admin.register(APIAccessRequest)
class APIAccessRequestAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_email', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['company_name', 'contact_email', 'use_case']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'contact_email')
        }),
        ('Request Details', {
            'fields': ('use_case',)
        }),
        ('Status & Follow-up', {
            'fields': ('status', 'reviewed_at', 'api_key_issued_at', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_reviewing', 'mark_as_approved', 'mark_as_credentials_sent']

    def mark_as_reviewing(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='reviewing', reviewed_at=timezone.now())
        self.message_user(request, f'{updated} request(s) marked as Under Review.')
    mark_as_reviewing.short_description = "Mark selected as Under Review"

    def mark_as_approved(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} request(s) marked as Approved.')
    mark_as_approved.short_description = "Mark selected as Approved"

    def mark_as_credentials_sent(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='credentials_sent', api_key_issued_at=timezone.now())
        self.message_user(request, f'{updated} request(s) marked as Credentials Sent.')
    mark_as_credentials_sent.short_description = "Mark selected as Credentials Sent"
