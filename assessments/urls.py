from django.urls import path

from . import views

app_name = "assessments"

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path(
        "invitations/",
        views.InvitationCreateApiView.as_view(),
        name="invitation-create",
    ),
    path(
        "sessions/<uuid:session_uuid>/responses/",
        views.SessionResponseApiView.as_view(),
        name="session-responses",
    ),
    path("<slug:slug>/", views.AssessmentDetailView.as_view(), name="detail"),
]
