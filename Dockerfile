<<<<<<< HEAD
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-k", "gevent", "-w", "1", "--bind", "0.0.0.0:5000", "run:app"]
=======
# TriviaVerse Dockerfile (Chapter 22)
# Multi-stage build for optimal production image

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Non-root user
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/')" || exit 1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--worker-class", "gthread", "--threads", "2", "--timeout", "120", "run:app"]
>>>>>>> 17eed4956a9023b91824efa22d88e223085ea1be
