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

# Ensure Railway environment variables are available
# Railway should automatically pass these, but we'll be explicit
ARG OPENAI_API_KEY
ARG LLM_API_KEY
ARG ANTHROPIC_API_KEY
ARG SUPABASE_URL
ARG SUPABASE_SERVICE_KEY
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV LLM_API_KEY=${LLM_API_KEY}
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ENV SUPABASE_URL=${SUPABASE_URL}
ENV SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start the FastAPI application
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --access-log --log-level info"]
