from __future__ import annotations

import json
from typing import Any

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_seo_jsonld(metadata: dict[str, Any] | None) -> str:
    if not metadata:
        return ''
    structured_data = metadata.get('structured_data')
    if not structured_data:
        schema_type = metadata.get('schema_type')
        title = metadata.get('meta_title')
        description = metadata.get('meta_description')
        if not schema_type:
            return ''
        structured_data = {
            '@context': 'https://schema.org',
            '@type': schema_type,
            'name': title,
            'description': description,
        }
    try:
        payload = structured_data if isinstance(structured_data, (list, dict)) else json.loads(structured_data)
    except (TypeError, ValueError):
        return ''
    return mark_safe(f'<script type="application/ld+json">{json.dumps(payload)}</script>')
