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
]
