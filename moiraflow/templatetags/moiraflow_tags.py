from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Devuelve el valor correspondiente a una clave en un diccionario"""
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError, KeyError):
        return None

@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    return value * arg

@register.filter
def puede_editar(articulo, user):
    return user == articulo.autor or (hasattr(user, 'perfil') and user.perfil.es_administrador)