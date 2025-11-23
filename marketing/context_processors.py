from django.core.cache import cache

from .models import MARKETING_SETTINGS_CACHE_KEY, MarketingSettings


def marketing_settings(request):
    """
    Expose the marketing settings singleton to every template.
    Cached for a short period to avoid repeated database hits.
    """
    settings = cache.get(MARKETING_SETTINGS_CACHE_KEY)
    if settings is None:
        settings = MarketingSettings.objects.order_by("pk").first()
        cache.set(MARKETING_SETTINGS_CACHE_KEY, settings, 300)
    return {"marketing_settings": settings}
