from django.urls import path

from . import views

app_name = "console"

urlpatterns = [
    path("login/", views.ConsoleLoginView.as_view(), name="login"),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("marketing/", views.MarketingAssessmentListView.as_view(), name="marketing-list"),
    path("marketing/new/", views.MarketingAssessmentCreateView.as_view(), name="marketing-create"),
    path(
        "marketing/<uuid:uuid>/",
        views.MarketingAssessmentDetailView.as_view(),
        name="marketing-detail",
    ),
    path("pm/", views.ProductAssessmentListView.as_view(), name="pm-list"),
    path("pm/new/", views.ProductAssessmentCreateView.as_view(), name="pm-create"),
    path("pm/<uuid:uuid>/", views.ProductAssessmentDetailView.as_view(), name="pm-detail"),
    path("clients/", views.ClientAccountListView.as_view(), name="client-list"),
    path("reports/", views.ReportingOverviewView.as_view(), name="reports-overview"),
    path("behavioral/", views.BehavioralAssessmentListView.as_view(), name="behavioral-list"),
    path(
        "behavioral/new/",
        views.BehavioralAssessmentCreateView.as_view(),
        name="behavioral-create",
    ),
    path(
        "behavioral/<uuid:uuid>/",
        views.BehavioralAssessmentDetailView.as_view(),
        name="behavioral-detail",
    ),
    path("site-content/", views.SiteContentListView.as_view(), name="content-list"),
    path("site-content/new/", views.SiteContentCreateView.as_view(), name="content-create"),
    path("site-content/<int:pk>/", views.SiteContentUpdateView.as_view(), name="content-edit"),
    path("resource-library/", views.ResourceAssetListView.as_view(), name="resource-list"),
    path("resource-library/new/", views.ResourceAssetCreateView.as_view(), name="resource-create"),
    path("resource-library/<int:pk>/", views.ResourceAssetUpdateView.as_view(), name="resource-edit"),
]
