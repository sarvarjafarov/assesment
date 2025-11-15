from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import BlogPost


class BlogListView(ListView):
    template_name = "blog/list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        qs = BlogPost.objects.published()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured = (
            BlogPost.objects.published().filter(is_featured=True).first()
            if not self.request.GET.get("page")
            else None
        )
        context["featured_post"] = featured
        return context


class BlogDetailView(DetailView):
    template_name = "blog/detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return BlogPost.objects.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_posts"] = (
            BlogPost.objects.published()
            .exclude(pk=self.object.pk)
            .order_by("-published_at")[:3]
        )
        return context
