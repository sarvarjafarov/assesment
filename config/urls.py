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
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from blog.sitemaps import BlogPostSitemap, BlogCategorySitemap, StaticPagesSitemap, PublicAssessmentSitemap

sitemaps = {
    'posts': BlogPostSitemap,
    'categories': BlogCategorySitemap,
    'assessments': PublicAssessmentSitemap,
    'static': StaticPagesSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
