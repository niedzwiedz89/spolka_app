from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Pracownicy
    path("pracownicy/", views.pracownik_list, name="pracownik_list"),
    path("pracownicy/nowy/", views.pracownik_create, name="pracownik_create"),
    path("pracownicy/raport-budowy/", views.pracownik_raport_budowy, name="pracownik_raport_budowy"),
    path("pracownicy/<int:pk>/", views.pracownik_detail, name="pracownik_detail"),
    path("pracownicy/<int:pk>/usun/", views.pracownik_delete, name="pracownik_delete"),

    # Przypisania pracownik ↔ budowa
    path("pracownicy/<int:pracownik_pk>/przypisz/", views.przypisanie_create, name="przypisanie_create"),
    path("przypisanie/<int:pk>/usun/", views.przypisanie_delete, name="przypisanie_delete"),

    # Budowy
    path("budowy/", views.budowa_list, name="budowa_list"),
    path("budowy/nowy/", views.budowa_create, name="budowa_create"),
    path("budowy/<int:pk>/", views.budowa_detail, name="budowa_detail"),
    path("budowy/<int:pk>/usun/", views.budowa_delete, name="budowa_delete"),

    # Mieszkania
    path("mieszkania/", views.mieszkanie_list, name="mieszkanie_list"),
    path("mieszkania/nowy/", views.mieszkanie_create, name="mieszkanie_create"),
    path("mieszkania/<int:pk>/", views.mieszkanie_detail, name="mieszkanie_detail"),
    path("mieszkania/<int:pk>/usun/", views.mieszkanie_delete, name="mieszkanie_delete"),

    # Flota (Pojazdy)
    path("flota/", views.pojazd_list, name="pojazd_list"),
    path("flota/nowy/", views.pojazd_create, name="pojazd_create"),
    path("flota/<int:pk>/", views.pojazd_detail, name="pojazd_detail"),
    path("flota/<int:pk>/usun/", views.pojazd_delete, name="pojazd_delete"),

    # Zdarzenia floty
    path("flota/<int:pojazd_pk>/zdarzenie/", views.zdarzenie_create, name="zdarzenie_create"),
    path("zdarzenie/<int:pk>/usun/", views.zdarzenie_delete, name="zdarzenie_delete"),

    # Załączniki (uniwersalne)
    path("zalacznik/dodaj/<int:content_type_id>/<int:object_id>/", views.zalacznik_create, name="zalacznik_create"),
    path("zalacznik/<int:pk>/usun/", views.zalacznik_delete, name="zalacznik_delete"),
]
