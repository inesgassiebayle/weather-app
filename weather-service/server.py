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


def fetch_current_weather(lat: float, lon: float):

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

    if "current" in data and "current_units" in data:
        cur = data["current"]
        u = data["current_units"]
        return {
            "temperature": _to_float(cur.get("temperature_2m")),
            "windspeed": _to_float(cur.get("wind_speed_10m")),
            "humidity": _to_float(cur.get("relative_humidity_2m")),
            "precip_mm": _to_float(cur.get("precipitation")),
            "time": str(cur.get("time", "")),
            "unit_temperature": u.get("temperature_2m", "°C"),
            "unit_windspeed": u.get("wind_speed_10m", "km/h"),
        }

    params = {
        "latitude": lat,
        "longitude": lon,
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
            "precip_mm": _to_float(cw.get("precipitation")),
            "time": str(cw.get("time", "")),
            "unit_temperature": "°C",
            "unit_windspeed": "km/h",
        }

    raise RuntimeError("Unexpected Open-Meteo response")


class WeatherServiceServicer(pb_grpc.WeatherServiceServicer):
    def GetWeather(self, request, context):
        try:
            lat = float(request.lat)
            lon = float(request.lon)
        except Exception:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("lat/lon must be numbers")
            return pb.WeatherServiceResponse()

        try:
            w = fetch_current_weather(lat, lon)
            return pb.WeatherServiceResponse(
                temperature=w["temperature"],
                windspeed=w["windspeed"],
                observation_time=w["time"],
                unit_temperature=w["unit_temperature"],
                unit_windspeed=w["unit_windspeed"],
                humidity=w["humidity"],
                precip_mm=w["precip_mm"],
            )
        except requests.Timeout:
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Open-Meteo timed out")
            return pb.WeatherServiceResponse()
        except requests.HTTPError as e:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"Open-Meteo HTTP error: {e}")
            return pb.WeatherServiceResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb.WeatherServiceResponse()


def serve():
    port = os.getenv("WEATHER_PORT", "50052")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb_grpc.add_WeatherServiceServicer_to_server(WeatherServiceServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"weather-svc listening on {port}", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
