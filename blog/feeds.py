"""
RSS feed for blog posts.
Allows users to subscribe to blog updates via feed readers.
"""
from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import BlogPost


class BlogPostFeed(Feed):
    """RSS feed for published blog posts."""
    title = "Evalon Insights"
    link = "/blog/"
    description = "Latest hiring insights, product updates, and assessment best practices from Evalon."

    def items(self):
        """Return the 20 most recent published posts."""
        return BlogPost.objects.published()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_author_name(self, item):
        return item.display_author

    def item_categories(self, item):
        categories = []
        if item.category:
            categories.append(item.category.name)
        if item.pill_label:
            categories.append(item.pill_label)
        return categories
