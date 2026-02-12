"""
Sitemap configurations for blog, assessments, and static pages.
Used for SEO to help search engines discover and index content.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import BlogPost, BlogCategory
from pages.models import PublicAssessment, Role


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
            'pages:assessment_list',
            'pages:interview_questions_list',
            'pages:role_assessment_list',
            'blog:list',
        ]

    def location(self, item):
        return reverse(item)


class PublicAssessmentSitemap(Sitemap):
    """Sitemap for public assessment pages."""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return PublicAssessment.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class InterviewQuestionsSitemap(Sitemap):
    """Sitemap for interview question pages (one per role)."""
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        from django.db.models import Count, Q
        return Role.objects.filter(
            is_active=True,
        ).annotate(
            q_count=Count('interview_questions', filter=Q(interview_questions__is_active=True))
        ).filter(q_count__gt=0)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_interview_questions_url()


class RoleAssessmentSitemap(Sitemap):
    """Sitemap for role-based assessment pages."""
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Role.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
