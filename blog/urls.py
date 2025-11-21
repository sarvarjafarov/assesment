from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.BlogListView.as_view(), name="list"),
    path("<slug:slug>/", views.BlogDetailView.as_view(), name="detail"),
    path("preview/<slug:slug>/<uuid:token>/", views.BlogPreviewView.as_view(), name="preview"),
]
