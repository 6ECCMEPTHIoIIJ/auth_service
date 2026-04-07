FROM python:3.13-slim-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend_core /app/backend_core
COPY auth_service /app/auth_service

WORKDIR /app/auth_service

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e /app/backend_core \
    && pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
