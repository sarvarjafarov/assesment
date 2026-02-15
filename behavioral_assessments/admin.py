from django.contrib import admin

from .models import BehavioralQuestion, BehavioralAssessmentSession


@admin.register(BehavioralQuestion)
class BehavioralQuestionAdmin(admin.ModelAdmin):
    list_display = ['block_id', 'prompt_short', 'difficulty_level', 'is_active']
    list_filter = ['difficulty_level', 'is_active']
    search_fields = ['prompt']
    ordering = ['block_id']
    actions = ['mark_active', 'mark_inactive']

    def prompt_short(self, obj):
        return obj.prompt[:80]
    prompt_short.short_description = 'Prompt'

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} question(s) activated.')
    mark_active.short_description = "Activate selected questions"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} question(s) deactivated.')
    mark_inactive.short_description = "Deactivate selected questions"


@admin.register(BehavioralAssessmentSession)
class BehavioralAssessmentSessionAdmin(admin.ModelAdmin):
    list_display = ['candidate_id', 'status', 'eligibility_score', 'eligibility_label', 'level', 'created_at']
    list_filter = ['status', 'level']
    search_fields = ['candidate_id']
    readonly_fields = ['uuid', 'question_set', 'responses', 'trait_scores', 'profile_report', 'risk_flags', 'telemetry_log']
