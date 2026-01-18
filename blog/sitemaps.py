"""
Sitemap configurations for blog and static pages.
Used for SEO to help search engines discover and index content.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import BlogPost, BlogCategory


class BlogPostSitemap(Sitemap):
    """Sitemap for published blog posts."""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return BlogPost.objects.published()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class BlogCategorySitemap(Sitemap):
    """Sitemap for active blog categories."""
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return BlogCategory.objects.filter(is_active=True)

    def location(self, obj):
        return obj.get_absolute_url()


class StaticPagesSitemap(Sitemap):
    """Sitemap for static marketing pages."""
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return [
            'pages:home',
            'pages:contact',
            'pages:careers',
            'pages:security',
            'pages:privacy',
            'pages:terms',
            'pages:resources',
            'blog:list',
        ]

    def location(self, item):
        return reverse(item)
