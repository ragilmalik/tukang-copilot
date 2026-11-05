# Tukang Copilot: one container, one process (FastAPI serves the API and the phone web app).
# Render builds this from render.yaml; locally: docker compose up --build  ->  http://localhost:8000
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    DATA_DIR=/app/data

# ffmpeg: video clips and voice notes. DejaVu fonts: the PDF reports and the numbered part labels.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# Run as a normal user, not root. DATA_DIR holds photos and sessions (deleted after RETENTION_HOURS).
RUN useradd --create-home --uid 1000 app && mkdir -p /app/data && chown -R app:app /app/data
USER app

EXPOSE 8000
# Render ignores this (it uses healthCheckPath in render.yaml); docker / docker compose use it.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8000'), timeout=4)" || exit 1

# Render sets PORT (10000 by default). --proxy-headers makes https links and the visitor IP correct behind Render's proxy.
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --timeout-keep-alive 75 --no-server-header"]
