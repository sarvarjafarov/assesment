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
]
