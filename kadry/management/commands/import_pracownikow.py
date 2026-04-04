import os
import re
from django.core.management.base import BaseCommand
import openpyxl
from kadry.models import Pracownik

class Command(BaseCommand):
    help = "Importuje i aktualizuje pracowników z pliku Excel"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help="Ścieżka do pliku Excel")

    def handle(self, *args, **options):
        filepath = options['file']
        
        if not os.path.exists(filepath):
            self.stderr.write(f"Błąd: Plik '{filepath}' nie istnieje.")
            return

        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            ws = wb.active
        except Exception as e:
            self.stderr.write(f"Błąd otwarcia pliku {filepath}: {e}")
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        # Zaczynamy od wiersza 2, zakładając że w 1 jest nagłówek
        # Kolumny zg. z zrzutem:
        # A: Lp
        # B: Imię
        # C: Nazwisko
        # D: Pesel
        # E: Ulica Nr
        # F: Kod pocztowy (w tym miejscowosc e.g. "32-200 Miechów")
        # G: email
        # H: Dowód osobisty
        # I: Telefon

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            # Sprawdzamy czy wiersz nie jest po prostu pusty
            if not any(row):
                continue
                
            try:
                # Opcjonalne przypisania z odpowiednimi obcięciami
                imie_val = str(row[1] or "").strip()
                nazwisko_val = str(row[2] or "").strip()
                pesel_val = str(row[3] or "").strip()
                ulica_nr_val = str(row[4] or "").strip()
                kod_pelny_val = str(row[5] or "").strip()
                email_val = str(row[6] or "").strip()
                dowod_val = str(row[7] or "").strip()
                telefon_val = str(row[8] or "").strip()

                # Często liczby mogą wejść jako np "NaN" albo None -> po rzutowaniu "None" string
                if imie_val == "None": imie_val = ""
                if nazwisko_val == "None": nazwisko_val = ""
                if pesel_val == "None": pesel_val = ""
                if ulica_nr_val == "None": ulica_nr_val = ""
                if kod_pelny_val == "None": kod_pelny_val = ""
                if email_val == "None": email_val = ""
                if dowod_val == "None": dowod_val = ""
                if telefon_val == "None": telefon_val = ""

                # Pesel w Excelu może być traktowany jako int ucinany (na początku '00' usunięte).
                # Jeśli został np. "211501637" (9 znaków - stracił de facto zera).
                # Np. "00211501637" to 11 cyfr. Formułowanie do 11 zer.
                # Należy mieć jednak pewność że jest on samą cyfrą.
                if len(pesel_val) > 0 and pesel_val.isdigit():
                    pesel_val = pesel_val.zfill(11)

                if not pesel_val:
                    self.stdout.write(self.style.WARNING(f"Wiersz {row_idx}: Brak PESEL, pomijam. (Imię: {imie_val}, Nazwisko: {nazwisko_val})"))
                    skipped_count += 1
                    continue
                    
                # Wyłuskanie kodu pocztowego i miejscowości, format przeważnie "32-200 Miechów"
                kod_pocztowy = ""
                miejscowosc = ""
                
                # Proszuka xx-xxx
                match = re.match(r"(\d{2}-\d{3})\s*(.*)", kod_pelny_val)
                if match:
                    kod_pocztowy = match.group(1).strip()
                    miejscowosc = match.group(2).strip()
                else:
                    # Jak nie ma standardowego kodu to traktujemy całośc jako miejscowosc ew. wstawiamy do opisów.
                    miejscowosc = kod_pelny_val.strip()

                # update_or_create
                pracownik, created = Pracownik.objects.update_or_create(
                    pesel=pesel_val,
                    defaults={
                        'imie': imie_val[:100],
                        'nazwisko': nazwisko_val[:100],
                        'ulica_nr': ulica_nr_val[:200],
                        'kod_pocztowy': kod_pocztowy[:10],
                        'miejscowosc': miejscowosc[:150],
                        'email': email_val,
                        'dowod_osobisty': dowod_val[:20],
                        'telefon': telefon_val[:20],
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Wiersz {row_idx}: Wewnętrzny błąd - {e}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f"Import zakonczony! Dodano: {created_count}, Zaktualizowano: {updated_count}, Pominiętych (np. brak Pesel): {skipped_count}, Błędów: {error_count}"))
