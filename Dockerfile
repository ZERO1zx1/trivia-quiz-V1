FROM node:22-alpine AS frontend

WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend ./frontend
RUN npm run build

FROM python:3.12-slim AS wheels

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# FIX-016: system dependencies for building psycopg2; gcc is purged
# afterwards to shrink the image and reduce the attack surface.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN python -m pip install --upgrade pip \
    && python -m pip wheel --wheel-dir /wheels -r requirements.lock

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000 \
    TMPDIR=/tmp/triviaverse

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=wheels /wheels /wheels
COPY requirements.lock .
RUN python -m pip install --no-index --find-links=/wheels -r requirements.lock \
    && rm -rf /wheels

# Copy application code
COPY . .
COPY --from=frontend /build/app/static/js/vendor ./app/static/js/vendor

# FIX-016: directories are created BEFORE dropping to the non-root user
# so ownership is set while still running as root.
RUN useradd --create-home --system --uid 10001 appuser \
    && mkdir -p /tmp/triviaverse \
    && chown -R appuser:appuser /app /tmp/triviaverse
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, sys; \
urllib.request.urlopen('http://localhost:5000/health/live'); sys.exit(0)" || exit 1

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
