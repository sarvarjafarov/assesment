from django.contrib import admin

from .models import ProductQuestion, ProductAssessmentSession


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'question_type', 'category', 'difficulty_level', 'is_active']
    list_filter = ['question_type', 'category', 'difficulty_level', 'is_active']
    search_fields = ['question_text', 'explanation']
    ordering = ['category', '-created_at']
    actions = ['mark_active', 'mark_inactive']

    def question_text_short(self, obj):
        return obj.question_text[:80]
    question_text_short.short_description = 'Question'

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} question(s) activated.')
    mark_active.short_description = "Activate selected questions"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} question(s) deactivated.')
    mark_inactive.short_description = "Deactivate selected questions"


@admin.register(ProductAssessmentSession)
class ProductAssessmentSessionAdmin(admin.ModelAdmin):
    list_display = ['candidate_id', 'status', 'overall_score', 'level', 'created_at']
    list_filter = ['status', 'level']
    search_fields = ['candidate_id']
    readonly_fields = ['uuid', 'question_set', 'responses', 'category_breakdown', 'recommendations', 'telemetry_log']
