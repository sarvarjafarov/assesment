from django.db.models import Q
from django.http import Http404
from django.views.generic import DetailView, ListView

from .models import BlogPost, BlogCategory


class BlogListView(ListView):
    template_name = "blog/list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        qs = BlogPost.objects.published()
        # Category filtering
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogCategory.objects.filter(is_active=True)
        context['current_category'] = self.request.GET.get('category')
        return context


class BlogSearchView(ListView):
    """Search view for blog posts."""
    model = BlogPost
    template_name = "blog/search.html"
    context_object_name = "posts"
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        qs = BlogPost.objects.published()
        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(body__icontains=query) |
                Q(meta_keywords__icontains=query) |
                Q(author_name__icontains=query)
            ).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '').strip()
        context['categories'] = BlogCategory.objects.filter(is_active=True)
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
