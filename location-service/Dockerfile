FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements del location-service
COPY location-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos del location-service
COPY location-service/ .

# Copiar la carpeta proto
COPY proto/ ./proto/

EXPOSE 50051

CMD ["python", "LocationService.py"]
