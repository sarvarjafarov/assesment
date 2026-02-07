from __future__ import annotations

import re
from typing import Any, Pattern

from django.core.cache import cache
from django.db import models
from django.urls import reverse

from marketing.models import MARKETING_SETTINGS_CACHE_KEY, MarketingSettings


class SeoPageQuerySet(models.QuerySet):
    def ordered(self):
        return self.order_by('order', 'slug')


class SeoPage(models.Model):
    MATCH_EXACT = 'exact'
    MATCH_PREFIX = 'prefix'
    MATCH_REGEX = 'regex'
    MATCH_TYPE_CHOICES = [
        (MATCH_EXACT, 'Exact path match'),
        (MATCH_PREFIX, 'Path prefix match'),
        (MATCH_REGEX, 'Regex match'),
    ]

    slug = models.SlugField(unique=True)
    path = models.CharField(
        max_length=255,
        blank=True,
        help_text='Leading slash paths (e.g., /pricing) or regex when match_type=regex.',
    )
    match_type = models.CharField(max_length=16, choices=MATCH_TYPE_CHOICES, default=MATCH_EXACT)
    title = models.CharField(max_length=160, blank=True)
    description = models.CharField(max_length=320, blank=True)
    canonical_url = models.URLField(blank=True)
    og_title = models.CharField(max_length=160, blank=True)
    og_description = models.CharField(max_length=320, blank=True)
    og_type = models.CharField(max_length=50, blank=True, default='website')
    twitter_title = models.CharField(max_length=160, blank=True)
    twitter_description = models.CharField(max_length=320, blank=True)
    image_url = models.URLField(blank=True)
    meta_keywords = models.CharField(max_length=400, blank=True)
    schema_type = models.CharField(max_length=100, blank=True)
    structured_data = models.JSONField(blank=True, null=True)
    noindex = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    objects = SeoPageQuerySet.as_manager()

    class Meta:
        ordering = ['order', 'slug']
        verbose_name = 'SEO Page'
        verbose_name_plural = 'SEO Pages'

    def __str__(self) -> str:
        return self.slug

    def matches_path(self, path: str) -> bool:
        normalized = (path or '/').rstrip('/') or '/'
        candidate = (self.path or '').rstrip('/') or '/'
        if not self.path:
            return False
        if self.match_type == self.MATCH_EXACT:
            return candidate == normalized
        if self.match_type == self.MATCH_PREFIX:
            return normalized.startswith(candidate)
        if self.match_type == self.MATCH_REGEX:
            return bool(self._compiled_regex().match(path))
        return False

    def _compiled_regex(self) -> Pattern[str]:
        pattern = self.path or ''
        return re.compile(pattern)

    @classmethod
    def for_path(cls, path: str) -> 'SeoPage | None':
        for page in cls.objects.ordered():
            if page.matches_path(path):
                return page
        return None

    def metadata(self, defaults: dict[str, Any], request) -> dict[str, Any]:
        payload = {
            'meta_title': self.title or defaults.get('meta_title'),
            'meta_description': self.description or defaults.get('meta_description'),
            'og_title': self.og_title or self.title or defaults.get('meta_title'),
            'og_description': self.og_description or self.description or defaults.get('meta_description'),
            'og_type': self.og_type or defaults.get('og_type', 'website'),
            'twitter_title': self.twitter_title or self.title or defaults.get('meta_title'),
            'twitter_description': self.twitter_description or self.description or defaults.get('meta_description'),
            'canonical_url': self.canonical_url or defaults.get('canonical_url') or request.build_absolute_uri(),
            'image_url': self.image_url or defaults.get('image_url'),
            'meta_keywords': self.meta_keywords or defaults.get('meta_keywords'),
            'structured_data': self.structured_data or defaults.get('structured_data'),
            'schema_type': self.schema_type or defaults.get('schema_type'),
            'noindex': self.noindex,
        }
        return payload


def _get_marketing_settings() -> MarketingSettings | None:
    settings_obj = cache.get(MARKETING_SETTINGS_CACHE_KEY)
    if settings_obj is None:
        settings_obj = MarketingSettings.objects.order_by('pk').first()
        cache.set(MARKETING_SETTINGS_CACHE_KEY, settings_obj, 300)
    return settings_obj


def marketing_meta_defaults(request) -> dict[str, Any]:
    settings_obj = _get_marketing_settings()
    defaults: dict[str, Any] = {
        'meta_title': 'Evalon Assessments',
        'meta_description': 'Evalon helps recruitment teams design, deliver, and score behavioral assessments.',
        'og_type': 'website',
        'canonical_url': request.build_absolute_uri(),
        'image_url': None,
        'meta_keywords': None,
        'structured_data': None,
        'schema_type': None,
        'noindex': False,
    }
    if not settings_obj:
        return defaults
    defaults['meta_title'] = settings_obj.meta_title or defaults['meta_title']
    defaults['meta_description'] = settings_obj.meta_description or defaults['meta_description']
    defaults['meta_keywords'] = settings_obj.meta_keywords
    if settings_obj.has_meta_image:
        defaults['image_url'] = request.build_absolute_uri(reverse('marketing:meta-image'))
    return defaults
