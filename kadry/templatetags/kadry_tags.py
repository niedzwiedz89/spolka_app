from django import template

register = template.Library()


@register.filter
def attr(obj, name):
    """Pobiera atrybut obiektu po nazwie, np. {{ obj|attr:'imie' }}"""
    try:
        return getattr(obj, name, "")
    except Exception:
        return ""
@register.filter
def get_item(dictionary, key):
    """Pobiera element ze słownika po kluczu, np. {{ slownik|get_item:klucz }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""
