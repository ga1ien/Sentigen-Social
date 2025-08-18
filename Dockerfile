# Railway Dockerfile - Deploy Backend Only
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Ensure application root is on Python path for imports like `database.*`
ENV PYTHONPATH=/app

# Copy backend requirements
COPY social-media-module/backend/requirements-prod.txt ./requirements-prod.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy backend source code
COPY social-media-module/backend/ ./

# Explicitly ensure the database package is copied (some builders can exclude it inadvertently)
COPY social-media-module/backend/database /app/database
RUN ls -la /app/database || echo "database directory not found after copy"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start the FastAPI application using our startup script
CMD ["python", "start.py"]
