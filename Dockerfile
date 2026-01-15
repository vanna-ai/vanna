# Tecknoworks AI Agent - Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Build React frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontends/tecknoworks-chat/package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy frontend source
COPY frontends/tecknoworks-chat/ ./

# Build frontend
RUN npm run build

# Stage 2: Build Python backend
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Python package files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir flit && \
    pip install --no-cache-dir ".[fastapi,azureopenai]"

# Stage 3: Production runtime
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash appuser && \
    mkdir -p /app/static /app/demo-data && \
    chown -R appuser:appuser /app

# Copy installed packages from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser demo-data/urban_eats.sqlite ./demo-data/

# Copy built frontend assets
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/dist/ ./static/

# Copy entrypoint
COPY --chown=appuser:appuser entrypoint.py ./

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "entrypoint.py"]
