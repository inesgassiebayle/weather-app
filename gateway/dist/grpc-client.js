import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROTO_PATH = join(__dirname, '../proto/weatherapp.proto');
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});
const weatherappProto = grpc.loadPackageDefinition(packageDefinition);
const LOCATION_SERVICE_HOST = process.env.LOCATION_SERVICE_HOST;
const LOCATION_SERVICE_PORT = process.env.LOCATION_SERVICE_PORT;
const LOCATION_SERVICE_URL = `${LOCATION_SERVICE_HOST}:${LOCATION_SERVICE_PORT}`;
export function createGrpcClient() {
    const client = new weatherappProto.weatherapp.LocationService(LOCATION_SERVICE_URL, grpc.credentials.createInsecure());
    return client;
}
// Función de utilidad para hacer llamadas con timeout
export function callWithTimeout(call, timeoutMs = 5000) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('gRPC call timeout'));
        }, timeoutMs);
        call((error, response) => {
            clearTimeout(timeout);
            if (error) {
                reject(error);
            }
            else {
                resolve(response);
            }
        });
    });
}
