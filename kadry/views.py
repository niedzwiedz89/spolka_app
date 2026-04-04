from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages as django_messages
from django.contrib.contenttypes.models import ContentType

from .models import Pracownik, Budowa, PracownikBudowa, Mieszkanie, Pojazd, ZdarzenieFloty, Zalacznik
from .forms import (
    PracownikForm, BudowaForm, PracownikBudowaForm,
    MieszkanieForm, PojazdForm, ZdarzenieFlotyForm, ZalacznikForm
)


# =============================================================================
# Helper function for wildcard filtering
# =============================================================================

def get_wildcard_filter(field_name, value):
    """
    Zwraca obiekt Q na podstawie dopasowań ze znakami %:
    - '%' – po prostu zignoruj puste
    - 'M%ch%' – regex lub złożone dopasowania (tutaj dla uproszczenia rzutowane na contains)
    - 'Michal%' -> startswith
    - '%chal' -> endswith
    - '%Michal%' -> icontains
    - 'Michal' -> exact/icontains jako domyślne zachowanie (zachowujemy icontains dla kompatybilności wstecz)
    """
    if not value or value == '%':
        return Q()

    if value.startswith('%') and value.endswith('%'):
        # %tekst%
        stripped = value.strip('%')
        return Q(**{f"{field_name}__icontains": stripped})
    elif value.startswith('%'):
        # %tekst
        stripped = value.lstrip('%')
        return Q(**{f"{field_name}__iendswith": stripped})
    elif value.endswith('%'):
        # tekst%
        stripped = value.rstrip('%')
        return Q(**{f"{field_name}__istartswith": stripped})
    elif '%' in value:
        # np. M%ch%l - regex dla SQLite
        pattern = value.replace('%', '.*')
        return Q(**{f"{field_name}__iregex": f"^{pattern}$"})
    else:
        # domyślnie, bez %
        return Q(**{f"{field_name}__icontains": value})


# =============================================================================
# DASHBOARD
# =============================================================================

def dashboard(request):
    """Strona główna – pulpit z kafelkami modułów."""
    stats = {
        "pracownicy": Pracownik.objects.count(),
        "budowy": Budowa.objects.count(),
        "mieszkania": Mieszkanie.objects.count(),
        "pojazdy": Pojazd.objects.count(),
    }
    return render(request, "kadry/dashboard.html", {"stats": stats})


# =============================================================================
# PRACOWNICY
# =============================================================================

def pracownik_list(request):
    """Lista pracowników z filtrami."""
    qs = Pracownik.objects.all()

    # Filtry
    f_imie = request.GET.get("imie", "")
    f_nazwisko = request.GET.get("nazwisko", "")
    f_pesel = request.GET.get("pesel", "")
    f_telefon = request.GET.get("telefon", "")

    if f_imie:
        qs = qs.filter(get_wildcard_filter("imie", f_imie))
    if f_nazwisko:
        qs = qs.filter(get_wildcard_filter("nazwisko", f_nazwisko))
    if f_pesel:
        qs = qs.filter(get_wildcard_filter("pesel", f_pesel))
    if f_telefon:
        qs = qs.filter(get_wildcard_filter("telefon", f_telefon))

    paginator = Paginator(qs, 50)
    page = request.GET.get("strona", 1)
    objects = paginator.get_page(page)

    context = {
        "objects": objects,
        "module_name": "Pracownicy",
        "filters": {
            "imie": f_imie,
            "nazwisko": f_nazwisko,
            "pesel": f_pesel,
            "telefon": f_telefon,
        },
        "columns": [
            ("imie", "Imię"),
            ("nazwisko", "Nazwisko"),
            ("pesel", "PESEL"),
            ("get_status_display", "Status"),
            ("telefon", "Telefon"),
            ("email", "E-mail"),
            ("dowod_osobisty", "Dowód osobisty"),
        ],
        "detail_url_name": "pracownik_detail",
        "create_url_name": "pracownik_create",
        "delete_url_name": "pracownik_delete",
        "bulk_actions": [
            {"id": "example_action", "label": "Przykładowa akcja (test)", "url": "#"}
        ],
    }
    return render(request, "kadry/list.html", context)


def pracownik_detail(request, pk):
    """Szczegóły / edycja pracownika."""
    obj = get_object_or_404(Pracownik, pk=pk)
    if request.method == "POST":
        form = PracownikForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Zapisano zmiany.")
            return redirect("pracownik_detail", pk=obj.pk)
    else:
        form = PracownikForm(instance=obj)

    # Przypisane budowy
    przypisania = PracownikBudowa.objects.filter(pracownik=obj).select_related("budowa")
    przypisanie_form = PracownikBudowaForm(initial={"pracownik": obj})

    # Załączniki
    ct = ContentType.objects.get_for_model(Pracownik)
    zalaczniki = Zalacznik.objects.filter(content_type=ct, object_id=obj.pk)
    zalacznik_form = ZalacznikForm()

    context = {
        "form": form,
        "object": obj,
        "module_name": "Pracownik",
        "list_url_name": "pracownik_list",
        "przypisania": przypisania,
        "przypisanie_form": przypisanie_form,
        "zalaczniki": zalaczniki,
        "zalacznik_form": zalacznik_form,
        "content_type_id": ct.pk,
    }
    return render(request, "kadry/pracownik_form.html", context)


def pracownik_create(request):
    """Dodawanie nowego pracownika."""
    if request.method == "POST":
        form = PracownikForm(request.POST)
        if form.is_valid():
            obj = form.save()
            django_messages.success(request, "Dodano pracownika.")
            return redirect("pracownik_detail", pk=obj.pk)
    else:
        form = PracownikForm()

    context = {
        "form": form,
        "module_name": "Nowy pracownik",
        "list_url_name": "pracownik_list",
    }
    return render(request, "kadry/pracownik_form.html", context)


def pracownik_delete(request, pk):
    """Usuwanie pracownika."""
    obj = get_object_or_404(Pracownik, pk=pk)
    if request.method == "POST":
        obj.delete()
        django_messages.success(request, "Usunięto pracownika.")
        return redirect("pracownik_list")
    return render(request, "kadry/confirm_delete.html", {
        "object": obj,
        "module_name": "Pracownik",
        "list_url_name": "pracownik_list",
    })


# =============================================================================
# BUDOWY
# =============================================================================

def budowa_list(request):
    """Lista budów z filtrami."""
    qs = Budowa.objects.all()

    f_nazwa = request.GET.get("nazwa", "")
    f_miejsce = request.GET.get("miejsce", "")
    f_adres = request.GET.get("adres", "")

    if f_nazwa:
        qs = qs.filter(get_wildcard_filter("nazwa", f_nazwa))
    if f_miejsce:
        qs = qs.filter(get_wildcard_filter("miejsce", f_miejsce))
    if f_adres:
        qs = qs.filter(get_wildcard_filter("adres", f_adres))

    paginator = Paginator(qs, 50)
    page = request.GET.get("strona", 1)
    objects = paginator.get_page(page)

    context = {
        "objects": objects,
        "module_name": "Budowy",
        "filters": {
            "nazwa": f_nazwa,
            "miejsce": f_miejsce,
            "adres": f_adres,
        },
        "columns": [
            ("nazwa", "Nazwa"),
            ("miejsce", "Miejsce"),
            ("adres", "Adres"),
        ],
        "detail_url_name": "budowa_detail",
        "create_url_name": "budowa_create",
        "delete_url_name": "budowa_delete",
    }
    return render(request, "kadry/list.html", context)


def budowa_detail(request, pk):
    """Szczegóły / edycja budowy."""
    obj = get_object_or_404(Budowa, pk=pk)
    if request.method == "POST":
        form = BudowaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Zapisano zmiany.")
            return redirect("budowa_detail", pk=obj.pk)
    else:
        form = BudowaForm(instance=obj)

    przypisani = PracownikBudowa.objects.filter(budowa=obj).select_related("pracownik")

    context = {
        "form": form,
        "object": obj,
        "module_name": "Budowa",
        "list_url_name": "budowa_list",
        "przypisani": przypisani,
    }
    return render(request, "kadry/budowa_form.html", context)


def budowa_create(request):
    """Dodawanie nowej budowy."""
    if request.method == "POST":
        form = BudowaForm(request.POST)
        if form.is_valid():
            obj = form.save()
            django_messages.success(request, "Dodano budowę.")
            return redirect("budowa_detail", pk=obj.pk)
    else:
        form = BudowaForm()

    context = {
        "form": form,
        "module_name": "Nowa budowa",
        "list_url_name": "budowa_list",
    }
    return render(request, "kadry/budowa_form.html", context)


def budowa_delete(request, pk):
    """Usuwanie budowy."""
    obj = get_object_or_404(Budowa, pk=pk)
    if request.method == "POST":
        obj.delete()
        django_messages.success(request, "Usunięto budowę.")
        return redirect("budowa_list")
    return render(request, "kadry/confirm_delete.html", {
        "object": obj,
        "module_name": "Budowa",
        "list_url_name": "budowa_list",
    })


# =============================================================================
# PRZYPISANIE PRACOWNIK ↔ BUDOWA
# =============================================================================

def przypisanie_create(request, pracownik_pk):
    """Dodawanie przypisania pracownika do budowy."""
    pracownik = get_object_or_404(Pracownik, pk=pracownik_pk)
    if request.method == "POST":
        form = PracownikBudowaForm(request.POST)
        if form.is_valid():
            przypisanie = form.save(commit=False)
            przypisanie.pracownik = pracownik
            przypisanie.save()
            django_messages.success(request, "Przypisano do budowy.")
    return redirect("pracownik_detail", pk=pracownik_pk)


def przypisanie_delete(request, pk):
    """Usuwanie przypisania pracownika do budowy."""
    obj = get_object_or_404(PracownikBudowa, pk=pk)
    pracownik_pk = obj.pracownik.pk
    if request.method == "POST":
        obj.delete()
        django_messages.success(request, "Usunięto przypisanie.")
    return redirect("pracownik_detail", pk=pracownik_pk)


# =============================================================================
# MIESZKANIA
# =============================================================================

def mieszkanie_list(request):
    """Lista mieszkań z filtrami."""
    qs = Mieszkanie.objects.all()

    f_nazwa = request.GET.get("nazwa", "")
    f_miasto = request.GET.get("miasto", "")
    f_adres = request.GET.get("adres", "")

    if f_nazwa:
        qs = qs.filter(get_wildcard_filter("nazwa", f_nazwa))
    if f_miasto:
        qs = qs.filter(get_wildcard_filter("miasto", f_miasto))
    if f_adres:
        qs = qs.filter(get_wildcard_filter("adres", f_adres))

    paginator = Paginator(qs, 50)
    page = request.GET.get("strona", 1)
    objects = paginator.get_page(page)

    context = {
        "objects": objects,
        "module_name": "Mieszkania",
        "filters": {
            "nazwa": f_nazwa,
            "miasto": f_miasto,
            "adres": f_adres,
        },
        "columns": [
            ("nazwa", "Nazwa"),
            ("adres", "Adres"),
            ("miasto", "Miasto"),
            ("pojemnosc", "Pojemność"),
        ],
        "detail_url_name": "mieszkanie_detail",
        "create_url_name": "mieszkanie_create",
        "delete_url_name": "mieszkanie_delete",
    }
    return render(request, "kadry/list.html", context)


def mieszkanie_detail(request, pk):
    """Szczegóły / edycja mieszkania."""
    obj = get_object_or_404(Mieszkanie, pk=pk)
    if request.method == "POST":
        form = MieszkanieForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Zapisano zmiany.")
            return redirect("mieszkanie_detail", pk=obj.pk)
    else:
        form = MieszkanieForm(instance=obj)

    context = {
        "form": form,
        "object": obj,
        "module_name": "Mieszkanie",
        "list_url_name": "mieszkanie_list",
    }
    return render(request, "kadry/mieszkanie_form.html", context)


def mieszkanie_create(request):
    """Dodawanie nowego mieszkania."""
    if request.method == "POST":
        form = MieszkanieForm(request.POST)
        if form.is_valid():
            obj = form.save()
            django_messages.success(request, "Dodano mieszkanie.")
            return redirect("mieszkanie_detail", pk=obj.pk)
    else:
        form = MieszkanieForm()

    context = {
        "form": form,
        "module_name": "Nowe mieszkanie",
        "list_url_name": "mieszkanie_list",
    }
    return render(request, "kadry/mieszkanie_form.html", context)


def mieszkanie_delete(request, pk):
    """Usuwanie mieszkania."""
    obj = get_object_or_404(Mieszkanie, pk=pk)
    if request.method == "POST":
        obj.delete()
        django_messages.success(request, "Usunięto mieszkanie.")
        return redirect("mieszkanie_list")
    return render(request, "kadry/confirm_delete.html", {
        "object": obj,
        "module_name": "Mieszkanie",
        "list_url_name": "mieszkanie_list",
    })


# =============================================================================
# FLOTA (POJAZDY)
# =============================================================================

def pojazd_list(request):
    """Lista pojazdów z filtrami."""
    qs = Pojazd.objects.all()

    f_marka = request.GET.get("marka", "")
    f_nr_rej = request.GET.get("nr_rejestracyjny", "")
    f_model = request.GET.get("model_pojazdu", "")

    if f_marka:
        qs = qs.filter(get_wildcard_filter("marka", f_marka))
    if f_nr_rej:
        qs = qs.filter(get_wildcard_filter("nr_rejestracyjny", f_nr_rej))
    if f_model:
        qs = qs.filter(get_wildcard_filter("model_pojazdu", f_model))

    paginator = Paginator(qs, 50)
    page = request.GET.get("strona", 1)
    objects = paginator.get_page(page)

    context = {
        "objects": objects,
        "module_name": "Flota",
        "filters": {
            "marka": f_marka,
            "nr_rejestracyjny": f_nr_rej,
            "model_pojazdu": f_model,
        },
        "columns": [
            ("marka", "Marka"),
            ("model_pojazdu", "Model"),
            ("nr_rejestracyjny", "Nr rejestracyjny"),
            ("przebieg_km", "Przebieg (km)"),
            ("data_przegladu", "Przegląd"),
            ("data_ubezpieczenia", "Ubezpieczenie"),
        ],
        "detail_url_name": "pojazd_detail",
        "create_url_name": "pojazd_create",
        "delete_url_name": "pojazd_delete",
    }
    return render(request, "kadry/list.html", context)


def pojazd_detail(request, pk):
    """Szczegóły / edycja pojazdu + zdarzenia."""
    obj = get_object_or_404(Pojazd, pk=pk)
    if request.method == "POST":
        form = PojazdForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Zapisano zmiany.")
            return redirect("pojazd_detail", pk=obj.pk)
    else:
        form = PojazdForm(instance=obj)

    zdarzenia = ZdarzenieFloty.objects.filter(pojazd=obj).order_by("-data")
    zdarzenie_form = ZdarzenieFlotyForm()

    # Załączniki
    ct = ContentType.objects.get_for_model(Pojazd)
    zalaczniki = Zalacznik.objects.filter(content_type=ct, object_id=obj.pk)
    zalacznik_form = ZalacznikForm()

    context = {
        "form": form,
        "object": obj,
        "module_name": "Pojazd",
        "list_url_name": "pojazd_list",
        "zdarzenia": zdarzenia,
        "zdarzenie_form": zdarzenie_form,
        "zalaczniki": zalaczniki,
        "zalacznik_form": zalacznik_form,
        "content_type_id": ct.pk,
    }
    return render(request, "kadry/pojazd_form.html", context)


def pojazd_create(request):
    """Dodawanie nowego pojazdu."""
    if request.method == "POST":
        form = PojazdForm(request.POST)
        if form.is_valid():
            obj = form.save()
            django_messages.success(request, "Dodano pojazd.")
            return redirect("pojazd_detail", pk=obj.pk)
    else:
        form = PojazdForm()

    context = {
        "form": form,
        "module_name": "Nowy pojazd",
        "list_url_name": "pojazd_list",
    }
    return render(request, "kadry/pojazd_form.html", context)


def pojazd_delete(request, pk):
    """Usuwanie pojazdu."""
    obj = get_object_or_404(Pojazd, pk=pk)
    if request.method == "POST":
        obj.delete()
        django_messages.success(request, "Usunięto pojazd.")
        return redirect("pojazd_list")
    return render(request, "kadry/confirm_delete.html", {
        "object": obj,
        "module_name": "Pojazd",
        "list_url_name": "pojazd_list",
    })


# =============================================================================
# ZDARZENIA FLOTY
# =============================================================================

def zdarzenie_create(request, pojazd_pk):
    """Dodawanie zdarzenia do pojazdu."""
    pojazd = get_object_or_404(Pojazd, pk=pojazd_pk)
    if request.method == "POST":
        form = ZdarzenieFlotyForm(request.POST)
        if form.is_valid():
            zdarzenie = form.save(commit=False)
            zdarzenie.pojazd = pojazd
            zdarzenie.save()
            django_messages.success(request, "Dodano zdarzenie.")
    return redirect("pojazd_detail", pk=pojazd_pk)


def zdarzenie_delete(request, pk):
    """Usuwanie zdarzenia."""
    obj = get_object_or_404(ZdarzenieFloty, pk=pk)
    pojazd_pk = obj.pojazd.pk
    if request.method == "POST":
        obj.delete()
        django_messages.success(request, "Usunięto zdarzenie.")
    return redirect("pojazd_detail", pk=pojazd_pk)


# =============================================================================
# ZAŁĄCZNIKI (WIRTUALNE/GENERIC)
# =============================================================================

def zalacznik_create(request, content_type_id, object_id):
    """Uniwersalne dodawanie pliku do dowolnego obiektu."""
    ct = get_object_or_404(ContentType, pk=content_type_id)
    obj = ct.get_object_for_this_type(pk=object_id)

    if request.method == "POST":
        form = ZalacznikForm(request.POST, request.FILES)
        if form.is_valid():
            zalacznik = form.save(commit=False)
            zalacznik.content_type = ct
            zalacznik.object_id = obj.pk
            zalacznik.save()
            django_messages.success(request, "Poprawnie przesłano załącznik.")
        else:
            django_messages.error(request, "Błąd dodawania załącznika.")

    if ct.model == "pracownik":
        return redirect("pracownik_detail", pk=obj.pk)
    elif ct.model == "pojazd":
        return redirect("pojazd_detail", pk=obj.pk)
    return redirect("dashboard")


def zalacznik_delete(request, pk):
    """Usuwanie załącznika wraz z fizycznym plikiem."""
    zalacznik = get_object_or_404(Zalacznik, pk=pk)
    ct_model = zalacznik.content_type.model
    obj_pk = zalacznik.object_id

    if request.method == "POST":
        zalacznik.plik.delete(save=False) # fizyczne usuwanie z dysku
        zalacznik.delete()
        django_messages.success(request, "Usunięto załącznik i plik z serwera.")

    if ct_model == "pracownik":
        return redirect("pracownik_detail", pk=obj_pk)
    elif ct_model == "pojazd":
        return redirect("pojazd_detail", pk=obj_pk)
    return redirect("dashboard")
