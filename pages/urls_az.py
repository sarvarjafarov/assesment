from django.urls import path
from . import views_az

app_name = "pages_az"

urlpatterns = [
    path('', views_az.home, name='home'),
    path('qiymet/', views_az.pricing, name='pricing'),
    path('cv-yoxla/', views_az.resume_checker, name='resume_checker'),
    path('cv/', views_az.resume_builder_list, name='resume_builder_list'),
    path('cv/department/<slug:dept_slug>/', views_az.resume_builder_department, name='resume_builder_department'),
    path('cv/<slug:slug>/', views_az.resume_builder_detail, name='resume_builder_detail'),
    path('cv/<slug:slug>/yukle/', views_az.resume_download_pdf, name='resume_download_pdf'),
    path('elaqe/', views_az.contact, name='contact'),
    path('mexfilik/', views_az.privacy, name='privacy'),
    path('sertler/', views_az.terms, name='terms'),
]
