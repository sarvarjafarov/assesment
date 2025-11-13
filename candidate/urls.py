from django.urls import path

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
]
