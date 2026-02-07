from django.contrib import admin

from .models import SeoPage


@admin.register(SeoPage)
class SeoPageAdmin(admin.ModelAdmin):
    list_display = ('slug', 'path', 'match_type', 'title', 'noindex')
    list_filter = ('match_type', 'noindex')
    search_fields = ('slug', 'title', 'description', 'path')
    ordering = ('order', 'slug')
