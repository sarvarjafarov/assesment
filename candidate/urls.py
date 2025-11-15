from django.urls import path

from marketing_assessments import views_candidate as marketing_views

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
]
