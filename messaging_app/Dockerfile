# syntax=docker/dockerfile:1
FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Install system dependencies needed by some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Create a non-root user and switch to them later
RUN useradd --create-home appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy only requirements first to leverage Docker layer cache
COPY requirements.txt .

# Install Python dependencies (user install so no root-owned site-packages)
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Fix permissions and switch to non-root
RUN chown -R appuser:appuser /app
USER appuser

# Expose Django default port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=messaging_app.settings \
    PORT=8000

# Healthcheck (requires curl in image; we installed it)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Default command: use gunicorn if present; otherwise run Django dev server
CMD ["sh", "-c", "if command -v gunicorn >/dev/null 2>&1; then gunicorn messaging_app.wsgi:application --bind 0.0.0.0:${PORT} --workers 3; else python manage.py runserver 0.0.0.0:${PORT}; fi"]
