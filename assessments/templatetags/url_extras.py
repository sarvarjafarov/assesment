from django import template

register = template.Library()


@register.filter
def startswith(value, arg):
    """
    Safe `startswith` filter for template conditions.

    Usage: {% if request.path|startswith:"/clients" %}...{% endif %}
    """
    if value is None or arg is None:
        return False
    return str(value).startswith(str(arg))
