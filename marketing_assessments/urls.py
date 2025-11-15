from django.urls import path

from . import views, views_public

app_name = "marketing_assessments"

urlpatterns = [
    path("start/", views.StartAssessmentView.as_view(), name="start"),
    path("<str:candidate_id>/questions/", views.QuestionListView.as_view(), name="questions"),
    path("<str:candidate_id>/submit/", views.SubmitAssessmentView.as_view(), name="submit"),
    path("<str:candidate_id>/results/", views.AssessmentResultView.as_view(), name="results"),
    path("docs/api/", views_public.api_overview, name="api"),
]
