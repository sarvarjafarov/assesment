from collections import Counter

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import BlogPost


class BlogListView(ListView):
    template_name = "blog/list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        qs = BlogPost.objects.published()
        pillar = self.request.GET.get("pillar")
        if pillar:
            qs = qs.filter(pill_label__iexact=pillar)
        tag_query = self.request.GET.get("tag")
        if tag_query:
            qs = qs.filter(meta_keywords__icontains=tag_query)
        search_query = self.request.GET.get("q")
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query)
                | Q(excerpt__icontains=search_query)
                | Q(body__icontains=search_query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured_posts = []
        if not self.request.GET.get("page"):
            featured_posts = list(
                BlogPost.objects.published().filter(is_featured=True)[:5]
            )
            if not featured_posts:
                featured_posts = list(BlogPost.objects.published()[:3])
        context["featured_posts"] = featured_posts
        active_pillar = self.request.GET.get("pillar", "")
        context["active_pillar"] = active_pillar
        search_query = self.request.GET.get("q", "")
        context["search_query"] = search_query
        active_tag = self.request.GET.get("tag", "")
        context["active_tag"] = active_tag

        pillar_descriptions = {
            "product": "Platform updates and API launches.",
            "hiring ops": "Guides for talent teams & recruiters.",
            "gtm": "Growth + revenue leadership insights.",
            "behavioral science": "Research-backed interview tactics.",
        }
        stats = (
            BlogPost.objects.published()
            .values("pill_label", "pill_style")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        taxonomy = []
        for stat in stats:
            label = stat["pill_label"] or "Insights"
            normalized = label.lower()
            taxonomy.append(
                {
                    "label": label,
                    "count": stat["count"],
                    "style": stat["pill_style"] or "accent",
                    "description": pillar_descriptions.get(
                        normalized, f"Stories tagged {label}."
                    ),
                    "is_active": normalized == active_pillar.lower()
                    if active_pillar
                    else False,
                }
            )
        context["taxonomy"] = taxonomy
        latest_from = []
        for stat in stats[:3]:
            label = stat["pill_label"]
            if not label:
                continue
            latest = (
                BlogPost.objects.published()
                .filter(pill_label=label)
                .order_by("-published_at")
                .first()
            )
            if latest:
                latest_from.append(latest)
        context["latest_from_pillars"] = latest_from
        tag_counter = Counter()
        keywords_qs = (
            BlogPost.objects.published()
            .exclude(meta_keywords__isnull=True)
            .exclude(meta_keywords__exact="")
            .values_list("meta_keywords", flat=True)
        )
        for entry in keywords_qs:
            for raw in entry.split(","):
                tag = raw.strip()
                if tag:
                    tag_counter[tag] += 1
        tag_cloud = []
        for label, count in tag_counter.most_common(10):
            tag_cloud.append(
                {
                    "label": label,
                    "count": count,
                    "is_active": label.lower() == active_tag.lower()
                    if active_tag
                    else False,
                }
            )
        context["tag_cloud"] = tag_cloud
        list_configs = [
            {
                "title": "PM Assessment Playbook",
                "description": "Everything you need to benchmark PM candidates, build scorecards, and review insights with hiring managers.",
                "pillar": "product",
                "bg": "linear-gradient(135deg, #fef6ee, #fff)",
            },
            {
                "title": "Behavioral Science Series",
                "description": "Research-backed takes on soft skills, integrity checks, and structured interview loops.",
                "pillar": "behavioral science",
                "bg": "linear-gradient(135deg, #eef7ff, #fff)",
            },
            {
                "title": "Growth & GTM Toolkit",
                "description": "Stories for revenue leaders modernizing assessments for marketing, sales, and success roles.",
                "pillar": "gtm",
                "bg": "linear-gradient(135deg, #f5f0ff, #fff)",
            },
        ]
        reading_lists = []
        for block in list_configs:
            posts = list(
                BlogPost.objects.published()
                .filter(pill_label__iexact=block["pillar"])
                .order_by("-published_at")[:3]
            )
            if posts:
                reading_lists.append(
                    {
                        "title": block["title"],
                        "description": block["description"],
                        "bg": block["bg"],
                        "posts": posts,
                        "pillar": block["pillar"],
                    }
                )
        context["reading_lists"] = reading_lists
        context["top_reads"] = list(BlogPost.objects.published()[:5])
        context["proof_quotes"] = [
            {
                "company": "Northwind Talent",
                "quote": "“Sira’s blog gave us the blueprint for scoring PM assignments.”",
                "person": "Maya Patel",
                "role": "Head of Recruiting",
            },
            {
                "company": "Atlas GTM",
                "quote": "“We send every hiring manager the behavioral science series before interviews.”",
                "person": "Leo Ramirez",
                "role": "VP Sales",
            },
            {
                "company": "Loop AI Labs",
                "quote": "“The growth toolkit helped us standardize marketing trials globally.”",
                "person": "Sofia Nguyen",
                "role": "People Partner",
            },
        ]
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
