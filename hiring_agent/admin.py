from django.contrib import admin

from .models import AgentActionLog, HiringPipeline, PipelineCandidate


class PipelineCandidateInline(admin.TabularInline):
    model = PipelineCandidate
    extra = 0
    readonly_fields = (
        'candidate', 'stage', 'ai_screen_score', 'ai_final_score',
        'processed_at', 'decided_at',
    )
    fields = (
        'candidate', 'stage', 'ai_screen_score', 'ai_final_score',
        'human_decision', 'processed_at',
    )


@admin.register(HiringPipeline)
class HiringPipelineAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'status', 'automation_mode', 'candidate_count', 'created_at')
    list_filter = ('status', 'automation_mode', 'seniority_level')
    search_fields = ('title', 'client__company_name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    inlines = [PipelineCandidateInline]


@admin.register(PipelineCandidate)
class PipelineCandidateAdmin(admin.ModelAdmin):
    list_display = (
        'candidate', 'pipeline', 'stage', 'ai_screen_score',
        'ai_final_score', 'human_decision', 'created_at',
    )
    list_filter = ('stage', 'human_decision', 'pipeline__status')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email')
    readonly_fields = ('created_at', 'updated_at', 'processed_at', 'decided_at')


@admin.register(AgentActionLog)
class AgentActionLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'pipeline', 'candidate', 'status', 'tokens_used', 'duration_ms', 'created_at')
    list_filter = ('action', 'status')
    readonly_fields = ('created_at',)
