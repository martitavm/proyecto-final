from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Devuelve el valor correspondiente a una clave en un diccionario"""
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError, KeyError):
        return None