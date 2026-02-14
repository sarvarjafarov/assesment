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
    """Sitemap for static marketing pages with individual priorities."""

    # (url_name, changefreq, priority)
    _pages = [
        ('pages:home', 'daily', 1.0),
        ('pages:pricing', 'weekly', 0.9),
        ('pages:assessment_list', 'weekly', 0.9),
        ('pages:interview_questions_list', 'weekly', 0.8),
        ('pages:role_assessment_list', 'weekly', 0.8),
        ('blog:list', 'daily', 0.8),
        ('pages:contact', 'monthly', 0.7),
        ('pages:resources', 'monthly', 0.6),
        ('pages:careers', 'monthly', 0.5),
        ('pages:security', 'monthly', 0.4),
        ('pages:privacy', 'monthly', 0.3),
        ('pages:terms', 'monthly', 0.3),
    ]

    def items(self):
        return self._pages

    def location(self, item):
        return reverse(item[0])

    def changefreq(self, item):
        return item[1]

    def priority(self, item):
        return item[2]


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


class DepartmentIQSitemap(Sitemap):
    """Sitemap for department interview question landing pages."""
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        from pages.views import DEPARTMENT_META
        return list(DEPARTMENT_META.keys())

    def location(self, item):
        from django.urls import reverse
        return reverse('pages:interview_questions_department', kwargs={'dept_slug': item})


class DepartmentRoleSitemap(Sitemap):
    """Sitemap for department role assessment landing pages."""
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        from pages.views import DEPARTMENT_META
        return list(DEPARTMENT_META.keys())

    def location(self, item):
        from django.urls import reverse
        return reverse('pages:role_assessment_department', kwargs={'dept_slug': item})
