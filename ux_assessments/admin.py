from django.contrib import admin

from .models import UXDesignAssessmentSession, UXDesignQuestion


@admin.register(UXDesignQuestion)
class UXDesignQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "category", "question_type", "difficulty_level", "is_active")
    list_filter = ("category", "question_type", "difficulty_level", "is_active")
    search_fields = ("question_text",)
    ordering = ("-created_at",)
    actions = ["mark_active", "mark_inactive"]

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(UXDesignAssessmentSession)
class UXDesignAssessmentSessionAdmin(admin.ModelAdmin):
    list_display = ("candidate_id", "status", "overall_score", "created_at", "submitted_at")
    list_filter = ("status",)
    readonly_fields = (
        "uuid",
        "question_set",
        "responses",
        "hard_skill_score",
        "soft_skill_score",
        "overall_score",
        "category_breakdown",
        "recommendations",
    )
