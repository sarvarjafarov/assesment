"""
URL configuration for Custom Assessments.
"""
from django.urls import path

from . import views

app_name = "custom_assessments"

urlpatterns = [
    # Assessment CRUD
    path("", views.CustomAssessmentListView.as_view(), name="list"),
    path("create/", views.CustomAssessmentCreateView.as_view(), name="create"),
    path("<uuid:uuid>/", views.CustomAssessmentDetailView.as_view(), name="detail"),
    path("<uuid:uuid>/edit/", views.CustomAssessmentUpdateView.as_view(), name="edit"),
    path("<uuid:uuid>/delete/", views.CustomAssessmentDeleteView.as_view(), name="delete"),

    # Questions management
    path("<uuid:uuid>/questions/", views.QuestionsManageView.as_view(), name="questions"),
    path("<uuid:uuid>/questions/add/", views.QuestionCreateView.as_view(), name="question-add"),
    path("<uuid:uuid>/questions/<int:question_id>/edit/", views.QuestionUpdateView.as_view(), name="question-edit"),
    path("<uuid:uuid>/questions/<int:question_id>/delete/", views.QuestionDeleteView.as_view(), name="question-delete"),

    # Import methods
    path("<uuid:uuid>/upload-csv/", views.CSVUploadView.as_view(), name="upload-csv"),
    path("<uuid:uuid>/generate-ai/", views.AIGenerateView.as_view(), name="generate-ai"),
    path("csv-template/", views.CSVTemplateDownloadView.as_view(), name="csv-template"),

    # Assessment actions
    path("<uuid:uuid>/preview/", views.PreviewAssessmentView.as_view(), name="preview"),
    path("<uuid:uuid>/publish/", views.PublishView.as_view(), name="publish"),
    path("<uuid:uuid>/archive/", views.ArchiveView.as_view(), name="archive"),
    path("<uuid:uuid>/duplicate/", views.DuplicateView.as_view(), name="duplicate"),

    # Candidate management
    path("<uuid:uuid>/invite/", views.InviteCandidateView.as_view(), name="invite"),
    path("<uuid:uuid>/bulk-invite/", views.BulkInviteView.as_view(), name="bulk-invite"),
    path("session/<uuid:session_uuid>/", views.SessionResultView.as_view(), name="session-result"),
    path("session/<uuid:session_uuid>/update-score/", views.UpdateResponseScoreView.as_view(), name="update-response-score"),

    # Export
    path("<uuid:uuid>/export-questions/", views.ExportQuestionsView.as_view(), name="export-questions"),
]
