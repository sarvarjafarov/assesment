"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from blog.sitemaps import (
    BlogPostSitemap, BlogCategorySitemap, StaticPagesSitemap,
    PublicAssessmentSitemap, InterviewQuestionsSitemap, RoleAssessmentSitemap,
    DepartmentIQSitemap, DepartmentRoleSitemap,
)

sitemaps = {
    'posts': BlogPostSitemap,
    'categories': BlogCategorySitemap,
    'assessments': PublicAssessmentSitemap,
    'static': StaticPagesSitemap,
    'interview-questions': InterviewQuestionsSitemap,
    'role-assessments': RoleAssessmentSitemap,
    'department-iq': DepartmentIQSitemap,
    'department-roles': DepartmentRoleSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # Password reset flow (Django built-in views with custom templates)
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('', include('pages.urls')),
    path('blog/', include('blog.urls')),
    path('console/', include('console.urls')),
    path('candidate/', include('candidate.urls')),
    path('clients/', include('clients.urls')),
    path('clients/custom-assessments/', include('custom_assessments.urls')),
    path('api/assessments/', include('assessments.urls')),
    path('api/marketing-assessment/', include('marketing_assessments.urls')),
    path('api/pm-assessment/', include('pm_assessments.urls')),
    path('api/ux-assessment/', include('ux_assessments.urls')),
    path('api/hr-assessment/', include('hr_assessments.urls')),
    path('api/finance-assessment/', include('finance_assessments.urls')),
    path('marketing/', include('marketing.urls')),
    path('clients/hiring-agent/', include('hiring_agent.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
