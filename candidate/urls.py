from django.urls import path

from marketing_assessments import views_candidate as marketing_views
from pm_assessments import views_candidate as pm_views
from behavioral_assessments import views_candidate as behavioral_views

from . import views

app_name = "candidate"

urlpatterns = [
    path(
        "<uuid:session_uuid>/",
        views.SessionIntroView.as_view(),
        name="session-entry",
    ),
    path(
        "<uuid:session_uuid>/start/",
        views.SessionAssessmentView.as_view(),
        name="session-start",
    ),
    path(
        "<uuid:session_uuid>/complete/",
        views.SessionCompleteView.as_view(),
        name="session-complete",
    ),
    path(
        "marketing/<uuid:session_uuid>/",
        marketing_views.MarketingAssessmentView.as_view(),
        name="marketing-session",
    ),
    path(
        "marketing/<uuid:session_uuid>/complete/",
        marketing_views.MarketingAssessmentCompleteView.as_view(),
        name="marketing-complete",
    ),
    path(
        "marketing/<uuid:session_uuid>/expired/",
        marketing_views.MarketingAssessmentExpiredView.as_view(),
        name="marketing-expired",
    ),
    path(
        "pm/<uuid:session_uuid>/",
        pm_views.ProductAssessmentView.as_view(),
        name="pm-session",
    ),
    path(
        "pm/<uuid:session_uuid>/complete/",
        pm_views.ProductAssessmentCompleteView.as_view(),
        name="pm-complete",
    ),
    path(
        "pm/<uuid:session_uuid>/expired/",
        pm_views.ProductAssessmentExpiredView.as_view(),
        name="pm-expired",
    ),
    path(
        "behavioral/<uuid:session_uuid>/",
        behavioral_views.BehavioralAssessmentView.as_view(),
        name="behavioral-session",
    ),
    path(
        "behavioral/<uuid:session_uuid>/complete/",
        behavioral_views.BehavioralAssessmentCompleteView.as_view(),
        name="behavioral-complete",
    ),
    path(
        "behavioral/<uuid:session_uuid>/expired/",
        behavioral_views.BehavioralAssessmentExpiredView.as_view(),
        name="behavioral-expired",
    ),
]
