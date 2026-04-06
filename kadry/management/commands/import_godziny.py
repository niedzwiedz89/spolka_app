import os
import datetime
from django.core.management.base import BaseCommand
import openpyxl
from kadry.models import Pracownik, Budowa, PracownikBudowa

class Command(BaseCommand):
    help = "Pobiera dane dzienne z arkuszy Excel i wrzuca do PracownikBudowa"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help="Ścieżka do konkretnego pliku Excel")
        parser.add_argument('--dir', type=str, help="Ścieżka do folderu z pobranymi plikami Excel (np. media/reports/inbox)")

    def handle(self, *args, **options):
        # Definiujemy cel: albo dany plik, albo cały folder.
        filepath = options.get('file')
        dirpath = options.get('dir')

        if not filepath and not dirpath:
             # Użyjemy domyślnego folderu, w którym `fetch_reports_gmail` odkłada te pliki
             dirpath = os.path.join("media", "reports", "inbox")

        files_to_process = []
        if filepath:
            if os.path.exists(filepath):
                files_to_process.append(filepath)
            else:
                self.stderr.write(f"Plik {filepath} nie podsiada poprawnego wskazu.")
                return
        elif dirpath:
            if os.path.isdir(dirpath):
                for f in os.listdir(dirpath):
                    if f.endswith(('.xls', '.xlsx')):
                        files_to_process.append(os.path.join(dirpath, f))
            else:
                self.stderr.write(f"Katalog {dirpath} nie istnieje. Przypuszczalnie nie pobrano emaili.")
                return

        if not files_to_process:
            self.stdout.write("Brak plików excela do przetworzenia.")
            return

        total_created = 0
        total_updated = 0

        for fpath in files_to_process:
            self.stdout.write(f"\n--- Przetwarzanie pliku: {os.path.basename(fpath)} ---")
            try:
                if fpath.lower().endswith('.xls'):
                    import xlrd
                    wb = xlrd.open_workbook(fpath)
                    ws = wb.sheet_by_index(0)
                    rows = []
                    for r_idx in range(ws.nrows):
                        parsed_row = []
                        for c_idx in range(ws.ncols):
                            ctype = ws.cell_type(r_idx, c_idx)
                            cval = ws.cell_value(r_idx, c_idx)
                            if ctype == xlrd.XL_CELL_DATE:
                                dt = xlrd.xldate_as_datetime(cval, wb.datemode)
                                parsed_row.append(dt.date())
                            else:
                                parsed_row.append(cval)
                        rows.append(parsed_row)
                else:
                    wb = openpyxl.load_workbook(fpath, data_only=True)
                    ws = wb.active
                    rows = list(ws.iter_rows(values_only=True))
                if len(rows) < 2:
                    continue
                
                # Słownik indeks => Model Pracownika
                worker_columns = {}
                header_row_idx = 0
                
                # Skanowanie pierwszych 10 wierszy w poszukiwaniu nagłówków (ignorowanie pustych wierszy z początku)
                for h_idx, potential_header_row in enumerate(rows[:10]):
                    temp_workers = {}
                    col_idx = 1
                    while col_idx < len(potential_header_row) - 1:
                        h_val = str(potential_header_row[col_idx] or "").strip()
                        if h_val and len(h_val.split()) >= 2:
                            parts = h_val.split()
                            n_val, i_val = parts[0], parts[1]
                            pr = Pracownik.objects.filter(nazwisko__iexact=n_val, imie__iexact=i_val).first()
                            if pr:
                                temp_workers[col_idx] = pr
                        col_idx += 1  # Badamy każdą kolumnę bo struktura bywa przesunięta
                        
                    if len(temp_workers) > 0:
                        worker_columns = temp_workers
                        header_row_idx = h_idx
                        break

                if not worker_columns:
                    self.stdout.write("Nie rozpoznano żadnych pracowników w nagłówkach pliku.")
                    continue

                # Zczytywanie danych dopiero od wiersza pod nagłówkiem
                for r_idx in range(header_row_idx + 1, len(rows)):
                    row = rows[r_idx]
                    
                    if not row or not row[0]:
                        continue
                        
                    # 1. Parsowanie daty z pierwszej kolumny (0) e.g. "2/02/2026"
                    data_val = row[0]
                    parsed_date = None
                    if isinstance(data_val, datetime.datetime):
                        parsed_date = data_val.date()
                    elif isinstance(data_val, datetime.date):
                        parsed_date = data_val
                    else:
                        d_str = str(data_val).strip()
                        for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
                            try:
                                parsed_date = datetime.datetime.strptime(d_str, fmt).date()
                                break
                            except ValueError:
                                pass
                    
                    if not parsed_date:
                        continue # Jeśli nie umiemy wyciagnąć daty, pomijamy komorke
                        
                    # 2. Przechodzimy po przypisanych kolumnach pracowników (np. "x", "10,00")
                    for w_col, pracownik in worker_columns.items():
                        godziny_raw = str(row[w_col] or "").strip().lower()
                        budowa_raw = str(row[w_col+1] or "").strip()
                        
                        # Replikacja ignorująca "x", "", null itp
                        godziny = None
                        if godziny_raw and godziny_raw != "x":
                            try:
                                # Zamienia polskie dziesętne przecinki na kropkę!
                                g_float = float(godziny_raw.replace(',', '.'))
                                godziny = g_float
                            except ValueError:
                                pass
                                
                        if godziny is not None and budowa_raw:
                            # Szukaj lub utworz wpis samej nazwy budowy (bardzo elastyczny mechanizm bazowany na plikach de-u)
                            budowa_obj, _ = Budowa.objects.get_or_create(
                                nazwa=budowa_raw,
                                defaults={'miejsce': budowa_raw, 'adres': '-'}
                            )
                            
                            # Pracownik budowa - nadpisz jako ewidencję za ten własnie DZIEN
                            pb, created = PracownikBudowa.objects.update_or_create(
                                pracownik=pracownik,
                                budowa=budowa_obj,
                                data_od=parsed_date,
                                data_do=parsed_date, # Ponieważ od-do dotyczy teraz de facto tego konkretnego 1 dnia
                                defaults={
                                    'godziny': godziny
                                }
                            )
                            if created:
                                total_created += 1
                            else:
                                total_updated += 1
                                
                # (Opcjonalnie) Przerzuć przetworzony plik do archiwum... (os.replace...) by nie zaczytywać podwójnie!
                arch_dir = os.path.join(os.path.dirname(fpath), "archive")
                os.makedirs(arch_dir, exist_ok=True)
                os.replace(fpath, os.path.join(arch_dir, os.path.basename(fpath)))
                
            except Exception as e:
                self.stderr.write(f"Błąd podczas sczytywania wierszy z pliku: {e}")

        self.stdout.write(self.style.SUCCESS(f"\nGeneracja ukończona! Dodano nowych dniówek: {total_created}, zaktualizowano starszych styków: {total_updated}"))
