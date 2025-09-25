import requests

class DummyRequest:
    def __init__(self, ip):
        self.ip = ip

class LocationService:
    def getLocation(self, request):
        ip = request.ip
        response = requests.get(f"https://ipwho.is/{ip}?fields=latitude,longitude", timeout=5)
        location = response.json()
        return location
