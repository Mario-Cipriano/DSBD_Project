# Usa un'immagine base di Python (o l'immagine del tuo linguaggio di programmazione)
FROM python:3.10.10

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# Copia il tuo codice consumer Kafka nella directory di lavoro del container
COPY Metrics_scraper.py /app/Metrics_scraper.py

# Specifica il comando di avvio del tuo container
CMD ["python", "/app/Metrics_scraper.py"]