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


@register.filter(name='contains_group')
def contains_group(groups_queryset, group_name: str) -> bool:
    """Check if a queryset of groups contains a group with the given name"""
    try:
        return groups_queryset.filter(name=group_name).exists()
    except Exception:
        return False
