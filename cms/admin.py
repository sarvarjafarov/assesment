from django.contrib import admin

from .models import Article, Feature, MarketingCopy, Testimonial


@admin.register(MarketingCopy)
class MarketingCopyAdmin(admin.ModelAdmin):
    list_display = ("hero_heading", "updated_at")


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "publish_date", "order")
    list_editable = ("order",)
    list_filter = ("pill_class",)
    search_fields = ("title", "summary", "author")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "order")
    list_editable = ("order",)
    search_fields = ("name", "role", "quote")
