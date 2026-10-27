# ========================================================
# Etapa 1: Build del Frontend con Node.js
# ========================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copiar manifiestos e instalar dependencias
COPY frontend/package*.json ./
RUN npm install

# Copiar código fuente y compilar bundle de producción
COPY frontend/ ./
RUN npm run build

# ========================================================
# Etapa 2: Imagen de producción con Python 3.12 y FastAPI
# ========================================================
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del backend
COPY backend/app ./app
COPY backend/scripts ./scripts

# Copiar el frontend compilado en la carpeta /app/static
COPY --from=frontend-builder /app/frontend/dist ./static

# Variables de entorno
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Arrancar Uvicorn leyendo dinámicamente la variable PORT de Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
