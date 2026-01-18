from django.contrib import admin
from .models import DemoRequest, APIAccessRequest, NewsletterSubscriber, PublicAssessment


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


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'status', 'source', 'subscribed_at', 'emails_sent_count']
    list_filter = ['status', 'source', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at', 'unsubscribed_at', 'last_email_sent_at', 'emails_sent_count']
    ordering = ['-subscribed_at']

    fieldsets = (
        ('Subscriber Information', {
            'fields': ('email', 'status', 'source')
        }),
        ('Email Tracking', {
            'fields': ('last_email_sent_at', 'emails_sent_count')
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'unsubscribed_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_active', 'mark_as_unsubscribed', 'export_emails']

    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} subscriber(s) marked as active.')
    mark_as_active.short_description = "Mark selected as Active"

    def mark_as_unsubscribed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='unsubscribed', unsubscribed_at=timezone.now())
        self.message_user(request, f'{updated} subscriber(s) marked as unsubscribed.')
    mark_as_unsubscribed.short_description = "Mark selected as Unsubscribed"

    def export_emails(self, request, queryset):
        emails = list(queryset.filter(status='active').values_list('email', flat=True))
        self.message_user(request, f'Active emails: {", ".join(emails[:10])}{"..." if len(emails) > 10 else ""} ({len(emails)} total)')
    export_emails.short_description = "Show active emails (for copy)"


@admin.register(PublicAssessment)
class PublicAssessmentAdmin(admin.ModelAdmin):
    list_display = ['label', 'title', 'internal_code', 'is_active', 'is_featured', 'order', 'updated_at']
    list_filter = ['is_active', 'is_featured', 'difficulty_level']
    list_editable = ['is_active', 'is_featured', 'order']
    search_fields = ['title', 'label', 'internal_code', 'summary']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['preview_key', 'created_at', 'updated_at']
    ordering = ['order', 'title']

    fieldsets = (
        ('Identification', {
            'fields': ('title', 'slug', 'internal_code', 'label', 'subtitle')
        }),
        ('Description', {
            'fields': ('summary', 'description', 'overview_content'),
            'description': 'Summary is used for cards. Description and overview for detail page.'
        }),
        ('Visual', {
            'fields': ('icon_svg', 'featured_image'),
            'classes': ('collapse',),
            'description': 'icon_svg should be SVG code. featured_image is a URL.'
        }),
        ('Assessment Details', {
            'fields': ('duration_minutes', 'question_count', 'difficulty_level', 'focus_areas', 'stats')
        }),
        ('Skills & Content', {
            'fields': ('skills_tested', 'sample_questions', 'scoring_rubric'),
            'classes': ('collapse',)
        }),
        ('Use Cases & FAQs', {
            'fields': ('use_cases', 'faqs'),
            'classes': ('collapse',)
        }),
        ('CTA', {
            'fields': ('cta_label', 'cta_url'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'meta_image'),
            'classes': ('collapse',)
        }),
        ('Preview & Timestamps', {
            'fields': ('preview_key', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_featured', 'remove_from_featured', 'activate', 'deactivate']

    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} assessment(s) marked as featured.')
    mark_as_featured.short_description = "Mark as featured (show on homepage)"

    def remove_from_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} assessment(s) removed from featured.')
    remove_from_featured.short_description = "Remove from featured"

    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} assessment(s) activated.')
    activate.short_description = "Activate selected assessments"

    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} assessment(s) deactivated.')
    deactivate.short_description = "Deactivate selected assessments"
