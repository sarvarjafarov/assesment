from django.urls import path

from . import views

app_name = "candidate"

urlpatterns = [
    path(
        "<uuid:session_uuid>/",
        views.SessionEntryView.as_view(),
        name="session-entry",
    ),
    path(
        "<uuid:session_uuid>/complete/",
        views.SessionCompleteView.as_view(),
        name="session-complete",
    ),
]

