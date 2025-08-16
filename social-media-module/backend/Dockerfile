FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-prod.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy all application files
COPY . .

# Make sure all directories are copied
RUN ls -la /app/
RUN ls -la /app/models/ || echo "models directory not found"

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "start.py"]