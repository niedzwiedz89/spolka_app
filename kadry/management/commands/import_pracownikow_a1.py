import os
import datetime
from django.core.management.base import BaseCommand
import openpyxl
from kadry.models import Pracownik

class Command(BaseCommand):
    help = "Importuje statusy i daty dla pracowników"

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

        updated_count = 0
        skipped_count = 0
        error_count = 0

        # Funkcja parsująca ciąg "DD.MM.YYYY-DD.MM.YYYY" na (start_date, end_date)
        def parse_date_range(text):
            if not text: return None, None
            text = str(text).strip()
            if "-" in text:
                parts = text.split("-")
                return parse_single_date(parts[0]), parse_single_date(parts[1])
            return None, None

        # Funkcja parsująca pojedynczą datę z komórki która bywa stringiem albo datą
        def parse_single_date(val):
            if not val: return None
            if isinstance(val, datetime.datetime):
                return val.date()
            if isinstance(val, datetime.date):
                return val
            val_str = str(val).strip()
            # Spróbuj sparsować różne formaty
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
                try:
                    return datetime.datetime.strptime(val_str, fmt).date()
                except ValueError:
                    pass
            return None

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                continue

            try:
                # Kolumny A-J -> indeksy 0-9
                # A: 0 (L.p)
                # B: 1 (Imię)
                # C: 2 (Nazwisko)
                # D: 3 (Umowa Próbna)
                # E: 4 (Umowa określona)
                # F: 5 (Umowa nieokreślona / STATUS)
                # G: 6 (A1 od)
                # H: 7 (A1 do)
                # I: 8 (EKUZ)
                # J: 9 (Badania)

                imie_val = str(row[1] or "").strip()
                nazwisko_val = str(row[2] or "").strip()

                if not imie_val and not nazwisko_val:
                    continue
                
                # Zabezpieczenie przed dziwnymi pustymi spacjami w Excelach
                if imie_val == "None": imie_val = ""
                if nazwisko_val == "None": nazwisko_val = ""

                if not imie_val or not nazwisko_val:
                    self.stdout.write(self.style.WARNING(f"Wiersz {row_idx}: Brak Imienia lub Nazwiska. Pomijam."))
                    skipped_count += 1
                    continue

                pracownicy = list(Pracownik.objects.filter(imie__iexact=imie_val, nazwisko__iexact=nazwisko_val))
                
                if not pracownicy:
                    self.stdout.write(self.style.WARNING(f"Wiersz {row_idx}: Nie znaleziono {imie_val} {nazwisko_val} w bazie! Pomijam."))
                    skipped_count += 1
                    continue
                
                # Bierymy pierwszego z brzegu jesli dubel
                p = pracownicy[0]
                if len(pracownicy) > 1:
                    self.stdout.write(self.style.WARNING(f"Wiersz {row_idx}: Znaleziono {len(pracownicy)} osób {imie_val} {nazwisko_val}! Aktualizuję PIERWSZEGO (np. starszy wpis)."))

                # 1. UMOWY - wyciągamy przedziały z 3 i 4
                u_probna_od, u_probna_do = parse_date_range(row[3])
                if u_probna_od: p.umowa_probna_od = u_probna_od
                if u_probna_do: p.umowa_probna_do = u_probna_do

                u_okresl_od, u_okresl_do = parse_date_range(row[4])
                if u_okresl_od: p.umowa_okreslona_od = u_okresl_od
                if u_okresl_do: p.umowa_okreslona_do = u_okresl_do

                # 2. STATUS - kolumna 5
                status_raw = str(row[5] or "").strip().lower()
                if "rezygnacja" in status_raw:
                    p.status = "rezygnacja"
                elif "nieokre" in status_raw:
                    p.status = "nieokreslona"
                elif "określona" in status_raw or "okreslona" in status_raw:
                    p.status = "okreslona"

                # 3. A1 - 6 i 7
                a1_od = parse_single_date(row[6])
                a1_do = parse_single_date(row[7])
                if a1_od: p.a1_od = a1_od
                if a1_do: p.a1_do = a1_do

                # 4. EKUZ - przeważnie jedna data idąca na DO
                ekuz_raw = str(row[8] or "").strip()
                if ekuz_raw.upper() != "T":
                    ekuz_do = parse_single_date(row[8])
                    if ekuz_do: p.ekuz_do = ekuz_do

                # 5. Badania - też jedno w domyśle "badania_do"
                badania_do = parse_single_date(row[9])
                if badania_do: p.badania_do = badania_do

                p.save()
                updated_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Wiersz {row_idx}: Błąd przy przetwarzaniu {imie_val} {nazwisko_val} - {e}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f"Import zakonczony! Zaktualizowano (Update): {updated_count}, Pominiętych brakiem profilu w BD: {skipped_count}, Błędów logicznych: {error_count}"))
