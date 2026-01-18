from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('careers/', views.careers, name='careers'),
    path('security/', views.security, name='security'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('resources/', views.resources, name='resources'),
    path('subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('robots.txt', views.robots_txt, name='robots'),
    # Public assessments
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/<slug:slug>/', views.assessment_detail, name='assessment_detail'),
    path('assessments/preview/<slug:slug>/<uuid:token>/', views.assessment_preview, name='assessment_preview'),
]
