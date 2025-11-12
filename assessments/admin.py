from django.contrib import admin

from . import models


class ChoiceInline(admin.TabularInline):
    model = models.Choice
    extra = 1


class QuestionInline(admin.StackedInline):
    model = models.Question
    extra = 0
    show_change_link = True


@admin.register(models.RoleCategory)
class RoleCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "updated_at")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "summary")


@admin.register(models.Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "level",
        "duration_minutes",
        "is_active",
        "updated_at",
    )
    list_filter = ("category", "level", "is_active")
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [QuestionInline]


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("assessment", "order", "question_type", "prompt", "updated_at")
    list_filter = ("question_type", "assessment__category")
    ordering = ("assessment", "order")
    inlines = [ChoiceInline]


@admin.register(models.CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "headline", "updated_at")
    search_fields = ("first_name", "last_name", "email")


class ResponseInline(admin.TabularInline):
    model = models.Response
    extra = 0
    show_change_link = True


@admin.register(models.AssessmentSession)
class AssessmentSessionAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "candidate",
        "assessment",
        "status",
        "overall_score",
        "invited_at",
        "submitted_at",
    )
    list_filter = ("status", "assessment__category")
    search_fields = ("candidate__first_name", "candidate__last_name", "assessment__title")
    inlines = [ResponseInline]


@admin.register(models.Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("session", "question", "score", "updated_at")
    list_filter = ("question__assessment",)
    filter_horizontal = ("selected_choices",)
