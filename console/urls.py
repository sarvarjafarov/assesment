from django.urls import path

from . import views

app_name = "console"

urlpatterns = [
    path("login/", views.ConsoleLoginView.as_view(), name="login"),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("assessments/", views.AssessmentListView.as_view(), name="assessment-list"),
    path(
        "assessments/new/",
        views.AssessmentCreateView.as_view(),
        name="assessment-create",
    ),
    path(
        "assessments/<slug:slug>/",
        views.AssessmentDetailView.as_view(),
        name="assessment-detail",
    ),
    path(
        "assessments/<slug:slug>/edit/",
        views.AssessmentUpdateView.as_view(),
        name="assessment-edit",
    ),
    path(
        "assessments/<slug:slug>/questions/new/",
        views.QuestionCreateView.as_view(),
        name="question-create",
    ),
    path(
        "questions/<int:pk>/choices/new/",
        views.ChoiceCreateView.as_view(),
        name="choice-create",
    ),
    path("candidates/", views.CandidateListView.as_view(), name="candidate-list"),
    path(
        "candidates/<int:pk>/",
        views.CandidateDetailView.as_view(),
        name="candidate-detail",
    ),
    path(
        "sessions/<int:pk>/",
        views.SessionDetailView.as_view(),
        name="session-detail",
    ),
    path("invites/new/", views.InviteCreateView.as_view(), name="invite-create"),
    path("companies/", views.CompanyListView.as_view(), name="company-list"),
    path("companies/new/", views.CompanyCreateView.as_view(), name="company-create"),
    path(
        "companies/<slug:slug>/",
        views.CompanyDetailView.as_view(),
        name="company-detail",
    ),
    path(
        "companies/<slug:slug>/edit/",
        views.CompanyUpdateView.as_view(),
        name="company-edit",
    ),
    path(
        "companies/<slug:company_slug>/tasks/new/",
        views.PositionTaskCreateView.as_view(),
        name="position-task-create",
    ),
    path(
        "tasks/<slug:slug>/",
        views.PositionTaskDetailView.as_view(),
        name="position-task-detail",
    ),
    path(
        "tasks/<slug:slug>/edit/",
        views.PositionTaskUpdateView.as_view(),
        name="position-task-edit",
    ),
    path("blog/", views.BlogPostListView.as_view(), name="blog-list"),
    path("blog/new/", views.BlogPostCreateView.as_view(), name="blog-create"),
    path("blog/<slug:slug>/edit/", views.BlogPostUpdateView.as_view(), name="blog-edit"),
]
