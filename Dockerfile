# Production Multi-Stage Dockerfile for Kurra Cadastral GIS & Partition Service
FROM python:3.11-slim-bookworm AS builder

# Set build environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system C geospatial and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    libgdal-dev \
    libspatialindex-dev \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies in isolated wheel build
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Final lightweight runtime image
FROM python:3.11-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install runtime shared libraries for GEOS / GDAL / SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-c1v5 \
    libgdal32 \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code and cadastral databases
COPY kurra/ /app/kurra/
COPY data/ /app/data/
COPY app.py /app/app.py

# Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

EXPOSE 8000

# Run FastAPI production ASGI server
CMD ["sh", "-c", "uvicorn kurra.api.main:app --host 0.0.0.0 --port ${PORT}"]
