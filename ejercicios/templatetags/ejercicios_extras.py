# ejercicios/templatetags/ejercicios_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter para obtener valor de diccionario por key.
    Uso: {{ diccionario|get_item:key }}
    """
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    try:
        return dictionary[key]
    except (KeyError, TypeError):
        return None

@register.filter
def get_bloque_data(categoria_data, bloque_num):
    """
    Template filter específico para obtener datos de bloque.
    Convierte string a int si es necesario.
    """
    try:
        bloque_key = int(bloque_num) if isinstance(bloque_num, str) else bloque_num
        return categoria_data.get('bloques', {}).get(bloque_key)
    except (ValueError, AttributeError):
        return None