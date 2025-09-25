import requests
import os
import grpc
from concurrent import futures
from proto import weatherapp_pb2, weatherapp_pb2_grpc

class LocationService(weatherapp_pb2_grpc.LocationServiceServicer):
    def getLocation(self, request, context):
        ip = request.ip
        response = requests.get(f"https://ipwho.is/{ip}?fields=latitude,longitude", timeout=5)
        location = response.json()
        return weatherapp_pb2.LocationCoordinates(
            lat=location.get("latitude", 0.0),
            lon=location.get("longitude", 0.0),
        )

def serve():
    port = os.getenv("LOCATION_PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    weatherapp_pb2_grpc.add_LocationServiceServicer_to_server(LocationService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"🚀 LocationService escuchando en puerto {port}")
    print(f"📍 Endpoint: [::]:{port}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("🛑 Deteniendo LocationService...")
        server.stop(0)

if __name__ == "__main__":
    serve()