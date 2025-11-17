from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("signup/", views.ClientSignupView.as_view(), name="signup"),
    path("signup/complete/", views.ClientSignupCompleteView.as_view(), name="signup-complete"),
    path("login/", views.ClientLoginView.as_view(), name="login"),
    path("logout/", views.ClientLogoutView.as_view(), name="logout"),
    path("dashboard/", views.ClientDashboardView.as_view(), name="dashboard"),
]
