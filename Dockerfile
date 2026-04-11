# Stosujemy lekką, czystą wersję Python 3.12
FROM python:3.12-slim

# Zabezpieczenie przed zapisem plików .pyc i buforowaniem przez pythona standardowego wyjścia
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalacja podstawowych narzędzi systemowych jeśli potrzebne są np do kompilacji
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Obszar roboczy w kontenerze dla Twojego kodu
WORKDIR /app

# Kopiowanie tylko pliku konfiguracyjnego w celu wykorzystania silnego chace'a Dockera
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

ENV CACHE_BUST=1

# Skopiowanie całego kodu źródłowego (oprócz ignorowanych przez .dockerignore) do katalogu roboczego
COPY . /app/

# Wystawienie portu Gunicorna
EXPOSE 8000

# Zbieramy pliki poleceniem collectstatic zaraz przed komendą startową gunicorna
CMD python manage.py collectstatic --no-input && gunicorn spolka_app.wsgi:application --bind 0.0.0.0:8000 --workers 3
