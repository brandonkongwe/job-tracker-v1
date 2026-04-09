# Stage 1: Build dependencies

FROM python:3.12-slim AS builder 

WORKDIR /app 

# Install system dependencies needed to compile psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a prefix directory
COPY requirements/ requirements/
RUN pip install --prefix=/install --no-cache-dir -r requirements/dev.txt


# Stage 2: Runtime image
FROM python:3.12-slim AS runtime
 
WORKDIR /app
 
# Only the runtime library needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
 
# Copy installed packages from builder
COPY --from=builder /install /usr/local
 
# Copy project source
COPY . .
 
# Collect static files
ENV DJANGO_SETTINGS_MODULE=jobtracker.settings.dev
RUN python manage.py collectstatic --noinput
 
# Create non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser
 
EXPOSE 8000
 
# Gunicorn: 2 workers per CPU core is a common starting point
CMD ["gunicorn", "jobtracker.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-"]