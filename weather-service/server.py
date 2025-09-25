import os
import requests
import grpc
from concurrent import futures

import weather_pb2
import weather_pb2_grpc

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def _to_float(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def fetch_current_weather(latitude: float, longitude: float):

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,relative_humidity_2m,precipitation",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "timezone": "auto",
    }
    r = requests.get(OPEN_METEO, params=params, timeout=6)
    r.raise_for_status()
    data = r.json()

    if "current" in data and "current_units" in data:
        cur = data["current"]
        u = data["current_units"]
        return {
            "temperature": _to_float(cur.get("temperature_2m")),
            "windspeed": _to_float(cur.get("wind_speed_10m")),
            "humidity": _to_float(cur.get("relative_humidity_2m")),
            "precipitation": _to_float(cur.get("precipitation")),
            "time": str(cur.get("time", "")),
            "unit_temperature": u.get("temperature_2m", "°C"),
            "unit_windspeed": u.get("wind_speed_10m", "km/h"),
        }

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
        "windspeed_unit": "kmh",
    }
    r2 = requests.get(OPEN_METEO, params=params, timeout=6)
    r2.raise_for_status()
    d2 = r2.json()
    cw = d2.get("current_weather")
    if cw:
        return {
            "temperature": _to_float(cw.get("temperature")),
            "windspeed": _to_float(cw.get("windspeed")),
            "humidity": _to_float(cw.get("relative_humidity")),
            "precipitation": _to_float(cw.get("precipitation")),
            "time": str(cw.get("time", "")),
            "unit_temperature": "°C",
            "unit_windspeed": "km/h",
        }

    raise RuntimeError("Unexpected Open-Meteo response")


class WeatherServicer(weather_pb2_grpc.WeatherServicer):
    def GetWeather(self, request, context):
        try:
            lat = float(request.latitude)
            lon = float(request.longitude)
        except Exception:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("latitude/longitude must be numbers")
            return weather_pb2.WeatherResponse()

        try:
            w = fetch_current_weather(lat, lon)
            return weather_pb2.WeatherResponse(
                temperature=w["temperature"],
                windspeed=w["windspeed"],
                observation_time=w["time"],
                unit_temperature=w["unit_temperature"],
                unit_windspeed=w["unit_windspeed"],
                humidity=w["humidity"],
                precipitation=w["precipitation"],
            )
        except requests.Timeout:
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Open-Meteo timed out")
            return weather_pb2.WeatherResponse()
        except requests.HTTPError as e:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"Open-Meteo HTTP error: {e}")
            return weather_pb2.WeatherResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return weather_pb2.WeatherResponse()


def serve():
    port = os.getenv("PORT", "50052")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    weather_pb2_grpc.add_WeatherServicer_to_server(WeatherServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"weather-svc listening on {port}", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
