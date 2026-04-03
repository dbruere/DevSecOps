FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Exposer le port de l'application Flask
EXPOSE 5000

ENV FLASK_APP=backend/app.py

# Lancer l'application
CMD ["flask", "run", "--host=0.0.0.0"]
