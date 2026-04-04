FROM python:3.11-slim

WORKDIR /app

# Empêche Python de générer des .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installer les dépendances maj et vider le cache 
RUN apt-get update && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Exposer le port
EXPOSE 5000

# Lancer avec Gunicorn (PROD)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:app"]
