from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("signup/", views.ClientSignupView.as_view(), name="signup"),
    path("signup/complete/", views.ClientSignupCompleteView.as_view(), name="signup-complete"),
    path("login/", views.ClientLoginView.as_view(), name="login"),
    path("logout/", views.ClientLogoutView.as_view(), name="logout"),
    path("dashboard/", views.ClientDashboardView.as_view(), name="dashboard"),
    path("dashboard/activity/export/", views.ClientActivityExportView.as_view(), name="activity-export"),
    path(
        "dashboard/assessments/<slug:assessment_type>/",
        views.ClientAssessmentManageView.as_view(),
        name="assessment-manage",
    ),
    path(
        "dashboard/assessments/<slug:assessment_type>/<uuid:session_uuid>/",
        views.ClientAssessmentDetailView.as_view(),
        name="assessment-detail",
    ),
]
