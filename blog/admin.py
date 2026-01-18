from django.contrib import admin

from .models import BlogPost, BlogCategory


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active", "post_count")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = "Posts"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "published_at", "updated_at", "is_featured")
    list_filter = ("status", "is_featured", "category", "pill_style")
    search_fields = ("title", "excerpt", "body", "author_name")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-published_at",)
    readonly_fields = ("created_at", "updated_at", "preview_key")
    autocomplete_fields = ("category",)
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "category", "status", "published_at")
        }),
        ("Content", {
            "fields": ("excerpt", "body", "hero_image")
        }),
        ("Display", {
            "fields": ("pill_label", "pill_style", "is_featured")
        }),
        ("Author", {
            "fields": ("author_name", "author_title")
        }),
        ("SEO", {
            "fields": ("meta_title", "meta_description", "meta_keywords", "meta_image"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("preview_key", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
