# Multi-stage Dockerfile for Memora Edge Platform
FROM python:3.11-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MEMORA_PROFILE=PRODUCTION

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY deployment/ ./deployment/
COPY experience/ ./experience/
COPY demo_experience.py .

EXPOSE 8000 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "demo_experience.py", "--scenario"]
