import os
import requests
import grpc
from concurrent import futures

from proto import weatherapp_pb2 as pb
from proto import weatherapp_pb2_grpc as pb_grpc

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def _to_float(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


class WeatherServiceServicer(pb_grpc.WeatherServiceServicer):
    def getWeather(self, request, context):
        lat = float(request.lat)
        lon = float(request.lon)

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,relative_humidity_2m,precipitation",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timezone": "auto",
        }
        r = requests.get(OPEN_METEO, params=params, timeout=6)
        r.raise_for_status()
        data = r.json()

        cur = data["current"]

        return pb.WeatherServiceResponse(
            temperature=_to_float(cur.get("temperature_2m")),
            windspeed=_to_float(cur.get("wind_speed_10m")),
            humidity=_to_float(cur.get("relative_humidity_2m")),
            precipitation= _to_float(cur.get("precipitation")),
        )


def serve():
    port = os.getenv("WEATHER_PORT")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb_grpc.add_WeatherServiceServicer_to_server(WeatherServiceServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
