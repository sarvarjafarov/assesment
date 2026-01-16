from django.contrib import admin
from .models import DemoRequest


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
