from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Devuelve el valor correspondiente a una clave en un diccionario"""
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError, KeyError):
        return None

@register.filter(name='rotate_degrees')
def rotate_degrees(index, total_days):
    """Calcula los grados para posicionar los días en el círculo"""
    return (index * 360) / total_days