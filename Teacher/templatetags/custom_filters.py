from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a key.
    Usage: {{ dictionary|get_item:key }}
    """
    try:
        return dictionary.get(str(key), 0)
    except (AttributeError, TypeError):
        return 0 