FROM python:3.11-slim
WORKDIR /app

COPY location-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY location-service/ ./

ENV PYTHONPATH="/app:/app/proto"
ENV LOCATION_PORT=50051
EXPOSE 50051

CMD ["python", "LocationService.py"]
