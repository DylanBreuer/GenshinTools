from django import template

register = template.Library()


@register.filter
def dictget(mapping, key):
    try:
        return mapping.get(key, 0)
    except Exception:
        return 0
