from django.http import Http404
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
        for related in context["recent_posts"]:
            if related.meta_keywords:
                tags = [tag.strip() for tag in related.meta_keywords.split(",") if tag.strip()]
                related.tag_list = tags[:2]
            else:
                related.tag_list = []
        return context


class BlogPreviewView(DetailView):
    template_name = "blog/detail.html"
    context_object_name = "post"

    def get_object(self, queryset=None):
        slug = self.kwargs.get("slug")
        token = self.kwargs.get("token")
        if not slug or not token:
            raise Http404
        try:
            post = BlogPost.objects.get(slug=slug)
        except BlogPost.DoesNotExist:
            raise Http404
        if str(post.preview_key) != str(token) and not self.request.user.is_staff:
            raise Http404
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["preview_mode"] = True
        return context
