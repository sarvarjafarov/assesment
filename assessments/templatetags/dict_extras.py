from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def dict_get(mapping, key):
    """Safely fetch a value from a dict-like object."""
    if not mapping:
        return None
    return mapping.get(key)
