from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def hide_site_footer(context):
    """Return True when the current path should suppress the marketing footer."""
    request = context.get("request")
    if not request:
        return False
    path = request.path or ""
    return path.startswith("/clients") or path.startswith("/console") or path.startswith("/candidate")
