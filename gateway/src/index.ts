import express from "express";
import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";

const PROTO_PATH = "./proto/weatherapp.proto";
const pkgDef = protoLoader.loadSync(PROTO_PATH, {});
const proto = grpc.loadPackageDefinition(pkgDef) as any;

const locationClient = new proto.weatherapp.LocationService(
  `${process.env.LOCATION_SERVICE_HOST || "location-service"}:${process.env.LOCATION_SERVICE_PORT || "50051"}`,
  grpc.credentials.createInsecure()
);
const weatherClient = new proto.weatherapp.WeatherService(
  `${process.env.WEATHER_SERVICE_HOST || "weather-service"}:${process.env.WEATHER_SERVICE_PORT || "50052"}`,
  grpc.credentials.createInsecure()
);

const app = express();

app.use(express.json());

app.get("/health", (_, res) => res.json({ ok: true }));

app.get("/location", (req, res) => {
  const ip = (req.query.ip as string) || getClientIp(req);
  
  if (!ip) {
    return res.status(400).json({ error: "IP address is required" });
  }

  locationClient.getLocation({ ip }, (err: any, location: any) => {
    if (err) {
      console.error("Location service error:", err);
      return res.status(400).json({ error: err.details || "Location service error" });
    }

    res.json({
      ip: ip,
      coordinates: { lat: location.lat, lon: location.lon }
    });
  });
});

function getClientIp(req: express.Request): string {
  return (req.headers['x-forwarded-for'] as string)?.split(',')[0] ||
         (req.headers['x-real-ip'] as string) ||
         req.connection.remoteAddress ||
         req.socket.remoteAddress ||
         '127.0.0.1';
}

app.get("/weather", (req, res) => {
  const ip = (req.query.ip as string) || getClientIp(req);
  
  if (!ip) {
    return res.status(400).json({ error: "IP address is required" });
  }

  locationClient.getLocation({ ip }, (err: any, location: any) => {
    if (err) {
      console.error("Location service error:", err);
      return res.status(400).json({ error: err.details || "Location service error" });
    }

    weatherClient.GetWeather({ lat: location.lat, lon: location.lon }, (werr: any, weather: any) => {
      if (werr) {
        console.error("Weather service error:", werr);
        return res.status(502).json({ error: werr.details || "Weather service error" });
      }

      res.json({
        ip: ip,
        coordinates: { lat: location.lat, lon: location.lon },
        weather: {
          temperature: weather.temperature,
          windspeed: weather.windspeed,
          humidity: weather.humidity,
          precipitation: weather.precip_mm,
          observation_time: weather.observation_time,
          units: {
            temperature: weather.unit_temperature,
            windspeed: weather.unit_windspeed
          }
        }
      });
    });
  });
});

const port = process.env.GATEWAY_PORT || 3000;
app.listen(port, () => console.log(`Gateway listening on port ${port}`));
