from django import template

register = template.Library()


@register.filter
def attr(obj, name):
    """Pobiera atrybut obiektu po nazwie, np. {{ obj|attr:'imie' }}.

    Dla pól z listą choices zwraca etykietę (get_<pole>_display), a nie surową wartość.
    """
    try:
        display = getattr(obj, f"get_{name}_display", None)
        if callable(display):
            return display()
        val = getattr(obj, name, "")
        if callable(val):
            return val()
        return val
    except Exception:
        return ""
@register.simple_tag(takes_context=True)
def strona_url(context, numer):
    """Link do strony paginacji z zachowaniem aktualnych filtrów w query stringu."""
    request = context.get("request")
    if request is None:
        return f"?strona={numer}"
    params = request.GET.copy()
    params["strona"] = numer
    return f"?{params.urlencode()}"


@register.filter
def get_item(dictionary, key):
    """Pobiera element ze słownika po kluczu, np. {{ slownik|get_item:klucz }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""
