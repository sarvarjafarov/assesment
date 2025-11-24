from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("signup/", views.ClientSignupView.as_view(), name="signup"),
    path("signup/complete/", views.ClientSignupCompleteView.as_view(), name="signup-complete"),
path("verify/<int:account_id>/<slug:token>/", views.ClientVerifyEmailView.as_view(), name="verify-email"),
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
    path(
        "dashboard/assessments/<slug:assessment_type>/<uuid:session_uuid>/export/",
        views.ClientAssessmentExportView.as_view(),
        name="assessment-export",
    ),
    path("dashboard/projects/", views.ClientProjectListView.as_view(), name="project-list"),
    path("dashboard/projects/<uuid:project_uuid>/", views.ClientProjectDetailView.as_view(), name="project-detail"),
    path("dashboard/projects/<uuid:project_uuid>/clone/", views.ClientProjectCloneView.as_view(), name="project-clone"),
    path(
        "dashboard/projects/<uuid:project_uuid>/pipeline/<slug:assessment_type>/<uuid:session_uuid>/",
        views.ClientProjectPipelineStageView.as_view(),
        name="project-pipeline-update",
    ),
]
