FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# FIX-016: system dependencies for building psycopg2; gcc is purged
# afterwards to shrink the image and reduce the attack surface.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt psycopg2-binary \
    && apt-get purge -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# FIX-016: directories are created BEFORE dropping to the non-root user
# so ownership is set while still running as root.
RUN mkdir -p logs static/uploads

# Create non-root user
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# FIX-016: stdlib-only healthcheck (no dependency on requests) against the
# dedicated /health endpoint instead of the HTML root.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, sys; \
urllib.request.urlopen('http://localhost:5000/health'); sys.exit(0)" || exit 1

CMD ["python", "run.py"]
