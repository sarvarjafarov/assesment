from django.urls import path

from . import views

app_name = 'hiring_agent'

urlpatterns = [
    path('upgrade/', views.UpgradeView.as_view(), name='upgrade'),
    path('', views.PipelineListView.as_view(), name='pipeline-list'),
    path('create/', views.PipelineCreateView.as_view(), name='pipeline-create'),
    path(
        '<uuid:pipeline_uuid>/',
        views.PipelineDetailView.as_view(),
        name='pipeline-detail',
    ),
    path(
        '<uuid:pipeline_uuid>/edit/',
        views.PipelineEditView.as_view(),
        name='pipeline-edit',
    ),
    path(
        '<uuid:pipeline_uuid>/upload/',
        views.ResumeUploadView.as_view(),
        name='resume-upload',
    ),
    path(
        '<uuid:pipeline_uuid>/process/',
        views.TriggerProcessView.as_view(),
        name='pipeline-process',
    ),
    path(
        '<uuid:pipeline_uuid>/pause/',
        views.PipelinePauseView.as_view(),
        name='pipeline-pause',
    ),
    path(
        '<uuid:pipeline_uuid>/stats/',
        views.PipelineStatsView.as_view(),
        name='pipeline-stats',
    ),
    path(
        '<uuid:pipeline_uuid>/candidates/<int:pk>/',
        views.CandidateDetailView.as_view(),
        name='candidate-detail',
    ),
    path(
        '<uuid:pipeline_uuid>/candidates/<int:pk>/review/',
        views.CandidateReviewView.as_view(),
        name='candidate-review',
    ),
]
