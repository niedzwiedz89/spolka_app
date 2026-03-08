from django.contrib import admin
from .models import Pracownik, Budowa, PracownikBudowa, Mieszkanie, Pojazd, ZdarzenieFloty


class PracownikBudowaInline(admin.TabularInline):
    model = PracownikBudowa
    extra = 1


class ZdarzenieFlotyInline(admin.TabularInline):
    model = ZdarzenieFloty
    extra = 1


@admin.register(Pracownik)
class PracownikAdmin(admin.ModelAdmin):
    list_display = ("nazwisko", "imie", "pesel", "telefon", "email")
    search_fields = ("nazwisko", "imie", "pesel")
    inlines = [PracownikBudowaInline]


@admin.register(Budowa)
class BudowaAdmin(admin.ModelAdmin):
    list_display = ("nazwa", "miejsce", "adres")
    search_fields = ("nazwa", "miejsce")
    inlines = [PracownikBudowaInline]


@admin.register(Mieszkanie)
class MieszkanieAdmin(admin.ModelAdmin):
    list_display = ("nazwa", "adres", "miasto", "pojemnosc")
    search_fields = ("nazwa", "miasto")


@admin.register(Pojazd)
class PojazdAdmin(admin.ModelAdmin):
    list_display = ("marka", "model_pojazdu", "nr_rejestracyjny", "przebieg_km")
    search_fields = ("marka", "nr_rejestracyjny")
    inlines = [ZdarzenieFlotyInline]


@admin.register(ZdarzenieFloty)
class ZdarzenieFlotyAdmin(admin.ModelAdmin):
    list_display = ("pojazd", "data", "typ", "koszt")
    list_filter = ("typ",)
