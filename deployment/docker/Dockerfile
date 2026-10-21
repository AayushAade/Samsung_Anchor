# MEMORA core image: text conversation, memory, diagnostics.
# Camera/microphone/face models are not included (see requirements-hardware.txt).
# Personal data lives in the /data volume, never in the image.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MEMORA_DB_PATH=/data/memora.sqlite

WORKDIR /app

# libgl/libglib are needed by opencv-python at import time.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# The text product needs no GUI: install the same OpenCV version as the headless build,
# which bundles no Qt and no FFmpeg device library (fewer LGPL components to redistribute).
RUN sed 's/^opencv-python==/opencv-python-headless==/' requirements.txt > /tmp/requirements-image.txt \
    && pip install --no-cache-dir -r /tmp/requirements-image.txt

COPY app.py health_check.py inspect_database.py ./
COPY config/ ./config/
COPY devices/ ./devices/
COPY src/ ./src/
COPY deployment/ ./deployment/
COPY experience/ ./experience/
COPY validation/ ./validation/

# Licence notices and a CycloneDX SBOM for exactly what is installed in the image.
RUN python deployment/generate_notices.py /app/licenses

RUN useradd --create-home --uid 10001 memora && mkdir -p /data /app/data/logs \
    && chown -R memora /data /app/data
USER memora
VOLUME ["/data"]

HEALTHCHECK --interval=60s --timeout=30s --start-period=20s --retries=3 \
  CMD python app.py --check || exit 1

# Interactive: docker run -it -v memora-data:/data memora
CMD ["python", "app.py", "--chat"]
