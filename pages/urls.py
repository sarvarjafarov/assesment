from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path('', views.home, name='home'),
    path('ai-hiring/', views.ai_hiring, name='ai_hiring'),
    path('pricing/', views.pricing, name='pricing'),
    path('contact/', views.contact, name='contact'),
    path('careers/', views.careers, name='careers'),
    path('careers/<slug:company_slug>/', views.company_careers, name='company_careers'),
    path('careers/<slug:company_slug>/<uuid:position_uuid>/', views.position_detail_public, name='position_detail_public'),
    path('careers/<slug:company_slug>/<uuid:position_uuid>/apply/', views.position_apply, name='position_apply'),
    path('careers/<slug:company_slug>/<uuid:position_uuid>/applied/', views.position_applied, name='position_applied'),
    path('security/', views.security, name='security'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('resources/', views.resources, name='resources'),
    path('subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('robots.txt', views.robots_txt, name='robots'),
    # Interview Questions (programmatic SEO)
    path('interview-questions/', views.interview_questions_list, name='interview_questions_list'),
    path('interview-questions/department/<slug:dept_slug>/', views.interview_questions_department, name='interview_questions_department'),
    path('interview-questions/<slug:slug>/', views.interview_questions_detail, name='interview_questions_detail'),
    # Role-Based Assessments (programmatic SEO)
    path('assessments/roles/', views.role_assessment_list, name='role_assessment_list'),
    path('assessments/roles/department/<slug:dept_slug>/', views.role_assessment_department, name='role_assessment_department'),
    path('assessments/for/<slug:slug>/', views.role_assessment_detail, name='role_assessment_detail'),
    # Public assessments
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/<slug:slug>/', views.assessment_detail, name='assessment_detail'),
    path('assessments/preview/<slug:slug>/<uuid:token>/', views.assessment_preview, name='assessment_preview'),
]
