# Railway Dockerfile - Deploy Backend Only
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY social-media-module/backend/requirements-prod.txt ./requirements-prod.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy backend source code
COPY social-media-module/backend/ ./

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start the FastAPI application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--access-log", "--log-level", "info"]
