FROM node:20-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EYEINSIGHT_DATA_DIR=/data \
    EYEINSIGHT_DATABASE_URL=sqlite:////data/eyeinsight.db \
    EYEINSIGHT_STATIC_DIR=/app/frontend_dist \
    EYEINSIGHT_MAX_ANALYSIS_FPS=4 \
    EYEINSIGHT_ANALYSIS_WIDTH=320

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /frontend/dist /app/frontend_dist
RUN mkdir -p /data/uploads /data/features

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
