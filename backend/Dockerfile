FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data/uploads /data/features

ENV EYEINSIGHT_DATA_DIR=/data \
    EYEINSIGHT_DATABASE_URL=sqlite:////data/eyeinsight.db
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
