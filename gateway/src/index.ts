import express from "express";
import path from "path";
import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";

const PROTO_PATH =
  process.env.PROTO_PATH || path.resolve(__dirname, "../../proto/weatherapp.proto");

const pkgDef = protoLoader.loadSync(PROTO_PATH, {
  keepCase: false,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});
const proto = grpc.loadPackageDefinition(pkgDef) as any;

const LOCATION_ADDR = `${process.env.LOCATION_SERVICE_HOST}:${
  process.env.LOCATION_SERVICE_PORT
}`;
const WEATHER_ADDR = `${process.env.WEATHER_SERVICE_HOST}:${
  process.env.WEATHER_SERVICE_PORT
}`;

const locationClient = new proto.weatherapp.LocationService(
  LOCATION_ADDR,
  grpc.credentials.createInsecure()
);
const weatherClient = new proto.weatherapp.WeatherService(
  WEATHER_ADDR,
  grpc.credentials.createInsecure()
);

const app = express();
app.use(express.json());

function getClientIp(req: express.Request): string | null {
  let ip = req.ip || req.socket.remoteAddress || null;
  if (!ip) return null;
  if (ip.startsWith("::ffff:")) ip = ip.slice(7);
  if (ip === "::1") ip = "127.0.0.1";
  return ip;
}

app.get("/weather", (req, res) => {
  const ipParam = (req.query.ip as string | undefined)?.trim();
  const ip = ipParam && ipParam.length > 0 ? ipParam : getClientIp(req);

  if (!ip) return res.status(400).json({ error: "IP address is required" });

  locationClient.getLocation({ ip }, (lerr: any, location: any) => {
    if (lerr) {
      const code = lerr.code === grpc.status.INVALID_ARGUMENT ? 400 : 502;
      return res.status(code).json({ error: lerr.details || "Location service error" });
    }
    if (!location) return res.status(502).json({ error: "Empty location response" });

    weatherClient.getWeather({ lat: location.lat, lon: location.lon }, (werr: any, weather: any) => {
      if (werr) {
        console.error("Weather service error:", werr);
        return res.status(502).json({ error: werr.details || "Weather service error" });
      }
      if (!weather) return res.status(502).json({ error: "Empty weather response" });

      return res.json({
        ip,
        coordinates: { lat: location.lat, lon: location.lon },
        weather: {
          temperature: weather.temperature,
          windspeed: weather.windspeed,
          humidity: weather.humidity,
          precipitation: weather.precipitation,
        },
      });
    });
  });
});


const port = Number(process.env.GATEWAY_PORT || 3000);
app.listen(port, () => {
  console.log(`Gateway listening on port ${port}`);
});
