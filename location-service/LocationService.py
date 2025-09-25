import requests
import os
import grpc
from concurrent import futures

class LocationService:
    def getLocation(self, request: L):
        ip = request.ip
        response = requests.get(f"https://ipwho.is/{ip}?fields=latitude,longitude", timeout=5)
        location = response.json()
        return location

def serve():
    port = os.getenv("LOCATION_PORT")
    locationServer = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # weatherapp_pb2_grpc.add_LocationServiceServicer_to_server(LocationService(), locationServer)
    locationServer.add_insecure_port(f"[::]:{port}")
    locationServer.start()
    print(f"LocationService escuchando en :{port}")
