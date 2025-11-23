from django.core.cache import cache
from django.urls import reverse

from .models import MARKETING_SETTINGS_CACHE_KEY, MarketingSettings


def marketing_settings(request):
    """
    Expose the marketing settings singleton and computed asset URLs.
    Cached for a short period to avoid repeated database hits.
    """
    settings = cache.get(MARKETING_SETTINGS_CACHE_KEY)
    if settings is None:
        settings = MarketingSettings.objects.order_by("pk").first()
        cache.set(MARKETING_SETTINGS_CACHE_KEY, settings, 300)

    meta_image_url = None
    if settings and settings.has_meta_image:
        meta_image_url = request.build_absolute_uri(reverse("marketing:meta-image"))

    return {
        "marketing_settings": settings,
        "marketing_meta_image_url": meta_image_url,
    }
