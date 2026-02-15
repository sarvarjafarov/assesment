from django.contrib import admin

from .models import CustomAssessment, CustomQuestion, CustomAssessmentSession


class CustomQuestionInline(admin.TabularInline):
    model = CustomQuestion
    extra = 0
    fields = ["order", "question_text", "correct_answer", "difficulty_level", "category"]
    readonly_fields = ["ai_generated"]


@admin.register(CustomAssessment)
class CustomAssessmentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "client",
        "status",
        "question_count",
        "time_limit_minutes",
        "ai_generated",
        "created_at",
    ]
    list_filter = ["status", "ai_generated", "created_at"]
    search_fields = ["name", "client__company_name", "description"]
    readonly_fields = ["uuid", "created_at", "updated_at", "published_at"]
    inlines = [CustomQuestionInline]

    fieldsets = (
        (None, {
            "fields": ("uuid", "client", "name", "description", "status")
        }),
        ("Settings", {
            "fields": ("time_limit_minutes", "passing_score")
        }),
        ("AI Generation", {
            "fields": ("role_description", "skills_to_test", "ai_generated"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "published_at"),
        }),
    )


@admin.register(CustomQuestion)
class CustomQuestionAdmin(admin.ModelAdmin):
    list_display = [
        "order",
        "question_text_short",
        "assessment",
        "correct_answer",
        "difficulty_level",
        "category",
    ]
    list_filter = ["assessment", "difficulty_level", "ai_generated"]
    search_fields = ["question_text", "assessment__name"]
    readonly_fields = ["created_at", "updated_at"]

    def question_text_short(self, obj):
        return obj.question_text[:60] + "..." if len(obj.question_text) > 60 else obj.question_text
    question_text_short.short_description = "Question"


@admin.register(CustomAssessmentSession)
class CustomAssessmentSessionAdmin(admin.ModelAdmin):
    list_display = [
        "candidate_id",
        "assessment",
        "client",
        "status",
        "score",
        "passed",
        "started_at",
        "completed_at",
    ]
    list_filter = ["status", "passed", "level", "created_at"]
    search_fields = ["candidate_id", "candidate_email", "assessment__name"]
    readonly_fields = [
        "uuid",
        "answers",
        "question_order",
        "score",
        "passed",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {
            "fields": ("uuid", "assessment", "client", "project", "candidate_id", "candidate_email")
        }),
        ("Progress", {
            "fields": ("status", "level", "current_question_index", "started_at", "completed_at")
        }),
        ("Results", {
            "fields": ("score", "passed", "answers"),
        }),
        ("Pipeline", {
            "fields": ("pipeline_stage", "pipeline_stage_updated_at", "deadline_at"),
        }),
        ("Internal", {
            "fields": ("question_order", "created_at", "updated_at"),
        }),
    )
