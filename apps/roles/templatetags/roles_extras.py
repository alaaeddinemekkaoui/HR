from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name: str) -> bool:
    try:
        return user.is_authenticated and user.groups.filter(name=group_name).exists()
    except Exception:
        return False


@register.filter(name='get_item')
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except Exception:
        return None
