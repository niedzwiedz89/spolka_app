from django import forms
from .models import Pracownik, Budowa, PracownikBudowa, Mieszkanie, Pojazd, ZdarzenieFloty, Zalacznik


class PracownikForm(forms.ModelForm):
    class Meta:
        model = Pracownik
        fields = [
            "imie", "nazwisko", "pesel", "status", "ulica_nr",
            "kod_pocztowy", "email", "telefon", "dowod_osobisty",
            "umowa_probna_od", "umowa_probna_do",
            "umowa_okreslona_od", "umowa_okreslona_do",
            "a1_od", "a1_do", "ekuz_od", "ekuz_do",
            "badania_od", "badania_do", "opis"
        ]
        widgets = {
            "imie": forms.TextInput(attrs={"class": "form-input"}),
            "nazwisko": forms.TextInput(attrs={"class": "form-input"}),
            "pesel": forms.TextInput(attrs={"class": "form-input", "maxlength": "11"}),
            "status": forms.Select(attrs={"class": "form-input"}),
            "ulica_nr": forms.TextInput(attrs={"class": "form-input"}),
            "kod_pocztowy": forms.TextInput(attrs={"class": "form-input", "placeholder": "00-000"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "dowod_osobisty": forms.TextInput(attrs={"class": "form-input"}),
            "telefon": forms.TextInput(attrs={"class": "form-input"}),
            "umowa_probna_od": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "umowa_probna_do": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "umowa_okreslona_od": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "umowa_okreslona_do": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "a1_od": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "a1_do": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "ekuz_od": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "ekuz_do": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "badania_od": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "badania_do": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "opis": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Ogólne informacje dodatkowe..."}),
        }


class BudowaForm(forms.ModelForm):
    class Meta:
        model = Budowa
        fields = ["nazwa", "miejsce", "adres"]
        widgets = {
            "nazwa": forms.TextInput(attrs={"class": "form-input"}),
            "miejsce": forms.TextInput(attrs={"class": "form-input"}),
            "adres": forms.TextInput(attrs={"class": "form-input"}),
        }


class PracownikBudowaForm(forms.ModelForm):
    class Meta:
        model = PracownikBudowa
        fields = ["budowa", "data_od", "data_do"]
        widgets = {
            "budowa": forms.Select(attrs={"class": "form-input"}),
            "data_od": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "data_do": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
        }


class MieszkanieForm(forms.ModelForm):
    class Meta:
        model = Mieszkanie
        fields = ["nazwa", "adres", "miasto", "pojemnosc", "uwagi"]
        widgets = {
            "nazwa": forms.TextInput(attrs={"class": "form-input"}),
            "adres": forms.TextInput(attrs={"class": "form-input"}),
            "miasto": forms.TextInput(attrs={"class": "form-input"}),
            "pojemnosc": forms.NumberInput(attrs={"class": "form-input", "min": "1"}),
            "uwagi": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }


class PojazdForm(forms.ModelForm):
    class Meta:
        model = Pojazd
        fields = [
            "marka", "model_pojazdu", "nr_rejestracyjny",
            "przebieg_km", "rok_produkcji", "data_przegladu", "data_ubezpieczenia",
        ]
        widgets = {
            "marka": forms.TextInput(attrs={"class": "form-input"}),
            "model_pojazdu": forms.TextInput(attrs={"class": "form-input"}),
            "nr_rejestracyjny": forms.TextInput(attrs={"class": "form-input"}),
            "przebieg_km": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "rok_produkcji": forms.NumberInput(attrs={"class": "form-input"}),
            "data_przegladu": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "data_ubezpieczenia": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
        }


class ZdarzenieFlotyForm(forms.ModelForm):
    class Meta:
        model = ZdarzenieFloty
        fields = ["data", "typ", "opis", "przebieg_km", "koszt"]
        widgets = {
            "data": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "typ": forms.Select(attrs={"class": "form-input"}),
            "opis": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
            "przebieg_km": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "koszt": forms.NumberInput(attrs={"class": "form-input", "step": "0.01"}),
        }


class ZalacznikForm(forms.ModelForm):
    class Meta:
        model = Zalacznik
        fields = ["plik", "typ_dokumentu", "opis"]
        widgets = {
            "plik": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "typ_dokumentu": forms.Select(attrs={"class": "form-input"}),
            "opis": forms.TextInput(attrs={"class": "form-input", "placeholder": "Krótki opis (opcjonalnie)"}),
        }
