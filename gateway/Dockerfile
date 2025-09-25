FROM node:18-alpine

WORKDIR /app

# Copiar package.json del gateway
COPY gateway/package*.json ./

RUN npm ci --only=production

# Copiar archivos del gateway
COPY gateway/ .

# Copiar la carpeta proto
COPY proto/ ./proto/

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]