from django.contrib import admin

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "published_at", "updated_at", "is_featured")
    list_filter = ("status", "is_featured", "pill_style")
    search_fields = ("title", "excerpt", "body", "author_name")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-published_at",)
    readonly_fields = ("created_at", "updated_at")
