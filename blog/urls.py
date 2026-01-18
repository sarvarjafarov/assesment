from django.urls import path

from . import views
from .feeds import BlogPostFeed

app_name = "blog"

urlpatterns = [
    path("", views.BlogListView.as_view(), name="list"),
    path("feed/", BlogPostFeed(), name="feed"),
    path("search/", views.BlogSearchView.as_view(), name="search"),
    path("<slug:slug>/", views.BlogDetailView.as_view(), name="detail"),
    path("preview/<slug:slug>/<uuid:token>/", views.BlogPreviewView.as_view(), name="preview"),
]
