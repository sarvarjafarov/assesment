from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("signup/", views.ClientSignupView.as_view(), name="signup"),
    path("signup/complete/", views.ClientSignupCompleteView.as_view(), name="signup-complete"),
path("verify/<int:account_id>/<slug:token>/", views.ClientVerifyEmailView.as_view(), name="verify-email"),
    path("login/", views.ClientLoginView.as_view(), name="login"),
    path("logout/", views.ClientLogoutView.as_view(), name="logout"),
    path("complete-profile/", views.CompleteProfileView.as_view(), name="complete_profile"),
    path("pending-approval/", views.PendingApprovalView.as_view(), name="pending_approval"),
    path("dashboard/", views.ClientDashboardView.as_view(), name="dashboard"),
    path("dashboard/activity/export/", views.ClientActivityExportView.as_view(), name="activity-export"),
    path("assessments/", views.ClientAssessmentsView.as_view(), name="assessments"),
    path("analytics/", views.ClientAnalyticsView.as_view(), name="analytics"),
    path("settings/", views.ClientSettingsView.as_view(), name="settings"),
    path("getting-started/", views.GettingStartedView.as_view(), name="getting-started"),
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
    path("dashboard/campaigns/", views.CampaignListView.as_view(), name="campaign-list"),
    path("dashboard/campaigns/<uuid:campaign_uuid>/", views.CampaignDetailView.as_view(), name="campaign-detail"),
    path("dashboard/campaigns/<uuid:campaign_uuid>/edit/", views.CampaignEditView.as_view(), name="campaign-edit"),
    path("dashboard/applications/", views.ApplicationListView.as_view(), name="application-list"),
    path("dashboard/applications/<uuid:application_uuid>/", views.ApplicationDetailView.as_view(), name="application-detail"),
    path("dashboard/applications/<uuid:application_uuid>/resume/", views.ApplicationResumeDownloadView.as_view(), name="application-resume"),
    path("dashboard/applications/<uuid:application_uuid>/send-assessment/", views.ApplicationSendAssessmentView.as_view(), name="application-send-assessment"),
    path("onboarding/complete/", views.OnboardingCompleteView.as_view(), name="onboarding-complete"),
    path("onboarding/reset/", views.OnboardingResetView.as_view(), name="onboarding-reset"),
    path("billing/", views.ClientBillingView.as_view(), name="billing"),
    path("support/request/", views.SupportRequestCreateView.as_view(), name="support-request"),
    path("api/notifications/", views.NotificationsAPIView.as_view(), name="api-notifications"),
    path("api/notifications/mark-read/", views.NotificationsMarkReadView.as_view(), name="api-notifications-mark-read"),
]
