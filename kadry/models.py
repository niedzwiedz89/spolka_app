from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Pracownik(models.Model):
    """Pracownik firmy."""
    STATUS_CHOICES = [
        ("nieokreslona", "Umowa nieokreślona"),
        ("okreslona", "Umowa określona"),
        ("probna", "Umowa próbna"),
        ("rezygnacja", "Rezygnacja / Zwolniony"),
    ]

    imie = models.CharField("Imię", max_length=100)
    nazwisko = models.CharField("Nazwisko", max_length=100)
    pesel = models.CharField("PESEL", max_length=11, unique=True)
    ulica_nr = models.CharField("Ulica i nr", max_length=200, blank=True)
    kod_pocztowy = models.CharField("Kod pocztowy", max_length=10, blank=True)
    miejscowosc = models.CharField("Miejscowość", max_length=150, blank=True)
    email = models.EmailField("E-mail", blank=True)
    dowod_osobisty = models.CharField("Dowód osobisty", max_length=20, blank=True)
    telefon = models.CharField("Telefon", max_length=20, blank=True)
    
    # Nowe pola ze statusami i datami
    status = models.CharField("Status pracownika", max_length=20, choices=STATUS_CHOICES, default="nieokreslona")
    
    umowa_probna_od = models.DateField("Umowa próbna (od)", null=True, blank=True)
    umowa_probna_do = models.DateField("Umowa próbna (do)", null=True, blank=True)
    
    umowa_okreslona_od = models.DateField("Umowa określona (od)", null=True, blank=True)
    umowa_okreslona_do = models.DateField("Umowa określona (do)", null=True, blank=True)
    
    a1_od = models.DateField("Aktualna A1 (od)", null=True, blank=True)
    a1_do = models.DateField("Aktualna A1 (do)", null=True, blank=True)
    
    ekuz_od = models.DateField("EKUZ (od)", null=True, blank=True)
    ekuz_do = models.DateField("EKUZ (do)", null=True, blank=True)
    
    badania_od = models.DateField("Badania (od)", null=True, blank=True)
    badania_do = models.DateField("Badania (do)", null=True, blank=True)
    
    opis = models.TextField("Dodatkowy opis", blank=True)

    data_utworzenia = models.DateTimeField("Data utworzenia", auto_now_add=True)

    class Meta:
        verbose_name = "Pracownik"
        verbose_name_plural = "Pracownicy"
        ordering = ["nazwisko", "imie"]

    def __str__(self):
        return f"{self.nazwisko} {self.imie}"


class Budowa(models.Model):
    """Budowa / plac budowy."""
    nazwa = models.CharField("Nazwa", max_length=200)
    miejsce = models.CharField("Miejsce", max_length=200, blank=True)
    adres = models.CharField("Adres", max_length=300, blank=True)

    class Meta:
        verbose_name = "Budowa"
        verbose_name_plural = "Budowy"
        ordering = ["nazwa"]

    def __str__(self):
        return self.nazwa


class PracownikBudowa(models.Model):
    """Przypisanie pracownika do budowy (M2M z dodatkowymi polami)."""
    pracownik = models.ForeignKey(
        Pracownik,
        on_delete=models.CASCADE,
        related_name="przypisania_budowy",
        verbose_name="Pracownik",
    )
    budowa = models.ForeignKey(
        Budowa,
        on_delete=models.CASCADE,
        related_name="przypisani_pracownicy",
        verbose_name="Budowa",
    )
    data_od = models.DateField("Data od", null=True, blank=True)
    data_do = models.DateField("Data do", null=True, blank=True)
    godziny = models.DecimalField("Liczba godzin", max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Przypisanie do budowy"
        verbose_name_plural = "Przypisania do budów"
        ordering = ["-data_od"]

    def __str__(self):
        return f"{self.pracownik} → {self.budowa}"


class Mieszkanie(models.Model):
    """Mieszkanie / kwatera dla pracowników."""
    nazwa = models.CharField("Nazwa", max_length=200)
    adres = models.CharField("Adres", max_length=300)
    miasto = models.CharField("Miasto", max_length=100, blank=True)
    pojemnosc = models.PositiveIntegerField("Pojemność (osób)", default=1)
    uwagi = models.TextField("Uwagi", blank=True)

    class Meta:
        verbose_name = "Mieszkanie"
        verbose_name_plural = "Mieszkania"
        ordering = ["nazwa"]

    def __str__(self):
        return f"{self.nazwa} ({self.miasto})"


class Pojazd(models.Model):
    """Pojazd we flocie firmowej."""
    marka = models.CharField("Marka", max_length=100)
    model_pojazdu = models.CharField("Model", max_length=100)
    nr_rejestracyjny = models.CharField(
        "Nr rejestracyjny", max_length=20, unique=True
    )
    przebieg_km = models.PositiveIntegerField("Przebieg (km)", default=0)
    rok_produkcji = models.PositiveIntegerField("Rok produkcji", null=True, blank=True)
    data_przegladu = models.DateField("Data przeglądu", null=True, blank=True)
    data_ubezpieczenia = models.DateField("Data ubezpieczenia", null=True, blank=True)

    class Meta:
        verbose_name = "Pojazd"
        verbose_name_plural = "Pojazdy"
        ordering = ["nr_rejestracyjny"]

    def __str__(self):
        return f"{self.marka} {self.model_pojazdu} ({self.nr_rejestracyjny})"


class ZdarzenieFloty(models.Model):
    """Zdarzenie / wpis w historii pojazdu."""

    TYP_CHOICES = [
        ("serwis", "Serwis"),
        ("naprawa", "Naprawa"),
        ("tankowanie", "Tankowanie"),
        ("wypadek", "Wypadek"),
        ("mandaty", "Mandaty"),
        ("przeglad", "Przegląd techniczny"),
        ("ubezpieczenie", "Ubezpieczenie"),
        ("inne", "Inne"),
    ]

    pojazd = models.ForeignKey(
        Pojazd,
        on_delete=models.CASCADE,
        related_name="zdarzenia",
        verbose_name="Pojazd",
    )
    data = models.DateField("Data")
    typ = models.CharField("Typ", max_length=30, choices=TYP_CHOICES, default="inne")
    opis = models.TextField("Opis", blank=True)
    przebieg_km = models.PositiveIntegerField("Przebieg (km)", null=True, blank=True)
    koszt = models.DecimalField(
        "Koszt (PLN)", max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = "Zdarzenie floty"
        verbose_name_plural = "Zdarzenia floty"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_typ_display()} – {self.pojazd} ({self.data})"


class Zalacznik(models.Model):
    """Uniwersalny model załącznika pozwalający podpinać pliki pod dowolny obiekt."""

    TYP_CHOICES = [
        ("dowod_przod", "Dowód osobisty - przód"),
        ("dowod_tyl", "Dowód osobisty - tył"),
        ("wzor_podpisu", "Wzór podpisu"),
        ("skan", "Skan dokumentu"),
        ("zdjecie", "Zdjęcie"),
        ("inne", "Inne"),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    plik = models.FileField("Plik", upload_to="zalaczniki/%Y/%m/")
    typ_dokumentu = models.CharField("Typ załącznika", max_length=50, choices=TYP_CHOICES, default="inne")
    opis = models.CharField("Opcjonalny opis", max_length=255, blank=True)
    data_dodania = models.DateTimeField("Data dodania", auto_now_add=True)

    class Meta:
        verbose_name = "Załącznik"
        verbose_name_plural = "Załączniki"
        ordering = ["-data_dodania"]

    def __str__(self):
        return f"{self.get_typ_dokumentu_display()} ({self.plik.name})"
