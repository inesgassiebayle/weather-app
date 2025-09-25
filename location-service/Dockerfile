FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY location-service/requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY location-service/LocationService.py .
COPY proto/ /app/proto/

EXPOSE 50051

CMD ["python", "LocationService.py"]
