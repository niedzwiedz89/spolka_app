"""Odczyt pozycji faktury z pliku XML KSeF (schemat FA, wariant 3).

Blob XML celowo nie jest polem modelu — wczytujemy go dopiero na żądanie,
żeby zapytania listy nie ciągnęły zawartości plików.
"""

import xml.etree.ElementTree as ET

from django.db import connection


def _nazwa(tag):
    return tag.split("}")[-1]


def _dziecko(element, nazwa):
    for child in element:
        if _nazwa(child.tag) == nazwa:
            return child
    return None


def _tekst(element, nazwa):
    child = _dziecko(element, nazwa)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def wczytaj_xml(ksef_number):
    """Zwraca zawartość pliku XML faktury albo None, jeśli nie został jeszcze pobrany."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT xml FROM ksef.invoice_xml WHERE ksef_number = %s",
            [ksef_number],
        )
        row = cur.fetchone()
    return bytes(row[0]) if row else None


def pozycje_faktury(xml_bytes):
    """Zwraca listę pozycji (FaWiersz) w skróconej postaci."""
    fa = _dziecko(ET.fromstring(xml_bytes), "Fa")
    if fa is None:
        return []

    pozycje = []
    for wiersz in fa:
        if _nazwa(wiersz.tag) != "FaWiersz":
            continue
        pozycje.append({
            "nr": _tekst(wiersz, "NrWierszaFa"),
            "nazwa": _tekst(wiersz, "P_7"),
            "jednostka": _tekst(wiersz, "P_8A"),
            "ilosc": _tekst(wiersz, "P_8B"),
            "cena_netto": _tekst(wiersz, "P_9A"),
            "wartosc_netto": _tekst(wiersz, "P_11"),
            "vat_kwota": _tekst(wiersz, "P_11Vat"),
            "stawka_vat": _tekst(wiersz, "P_12"),
        })
    return pozycje
