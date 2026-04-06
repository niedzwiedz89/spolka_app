import os
import base64
from django.core.management.base import BaseCommand
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

class Command(BaseCommand):
    help = "Pobiera zalaczniki typu xls/xlsx z Gmail za pomoca Service Account"

    def handle(self, *args, **options):
        # Wymuszamy zaczytanie zmiennych środowiskowych z ukrytego .env
        load_dotenv()
        
        my_mail = os.environ.get('MY_MAIL')
        if not my_mail:
            self.stderr.write("Błąd: Zmienna środowiskowa MY_MAIL nie jest ustawiona w systemie.")
            return

        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not cred_path:
             self.stderr.write("Błąd: GOOGLE_APPLICATION_CREDENTIALS nieustawione.")
             return

        scopes = ['https://www.googleapis.com/auth/gmail.readonly']
        
        # Inicjalizacja certyfikatów i delegacja uprawnień (Domain-wide Delegation na użytkownika)
        try:
            creds = service_account.Credentials.from_service_account_file(cred_path, scopes=scopes)
            creds = creds.with_subject(my_mail)
        except Exception as e:
            self.stderr.write(f"Błąd inicjalizacji kluczy SA GCP: {e}")
            return

        # Połączenie do usługi Gmail API
        try:
            service = build('gmail', 'v1', credentials=creds)
        except Exception as e:
             self.stderr.write(f"Nie udało się połączyć z API: {e}")
             return

        query = "in:sent to:holger.mueller@bemontec.de filename:xls OR filename:xlsx"
        self.stdout.write(f"Odpytywanie Google o wiadomości z parametrem: '{query}'...")

        try:
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
        except Exception as e:
            self.stderr.write(f"Błąd zapytania (sprawdź uprawnienia delegacji DWD w Google Workspace): {e}")
            return

        if not messages:
            self.stdout.write(self.style.WARNING("Twoja skrzynka nie posiada żadnych maili odpowiadających zapytaniu!"))
            return

        save_dir = os.path.join("media", "reports", "inbox")
        os.makedirs(save_dir, exist_ok=True)
        
        download_count = 0

        for msg in messages:
            msg_id = msg['id']
            try:
                # API pobiera pełną formatkę wiadomości
                message = service.users().messages().get(userId='me', id=msg_id).execute()
                
                # Skanowanie zagnieżdżeń (zwykłe i wieloczęściowe struktury maila)
                parts = []
                if 'parts' in message['payload']:
                    # Czasem zagnieżdżenia załączników potrafią być głębokie
                    def extract_parts(p_list):
                        extracted = []
                        for pt in p_list:
                            extracted.append(pt)
                            if 'parts' in pt:
                                extracted.extend(extract_parts(pt['parts']))
                        return extracted
                    parts = extract_parts(message['payload']['parts'])
                else:
                    parts = [message['payload']]

                for part in parts:
                    if part.get('filename') and part['filename'].lower().endswith(('.xls', '.xlsx')):
                        filename = part['filename']
                        filepath = os.path.join(save_dir, filename)
                        
                        # Nie pobieraj, jeśli plik już masz na serwerze
                        if os.path.exists(filepath):
                            continue
                            
                        # Czasem mały excel jest w ciele wiadomości pod kluczem 'data', częściej to duży plik załącznikowy z osobnym ID
                        body = part['body']
                        if 'data' in body:
                            data = body['data']
                        elif 'attachmentId' in body:
                            att_id = body['attachmentId']
                            att = service.users().messages().attachments().get(
                                userId='me', messageId=msg_id, id=att_id).execute()
                            data = att['data']
                        else:
                            continue
                        
                        file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                        with open(filepath, 'wb') as f:
                            f.write(file_data)
                            
                        self.stdout.write(self.style.SUCCESS(f"Sukces - Ściągnięto plik z serwerów Google: {filename}"))
                        download_count += 1
                        
            except Exception as e:
                self.stderr.write(f"Wystąpił błąd przy pobieraniu załącznika z maila o ID {msg_id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"\nOperacja ukończona. Pomyślnie zgrano na dysk {download_count} nowych raportów!"))
