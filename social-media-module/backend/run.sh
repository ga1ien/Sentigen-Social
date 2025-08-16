#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first to create the environment."
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please copy .env.example to .env and configure your settings."
    echo ""
    echo "Quick setup:"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your actual values"
    echo ""
fi

# Check if main application file exists
if [ -f "api/main.py" ]; then
    APP_MODULE="api.main:app"
    echo "🚀 Starting FastAPI server (api/main.py)..."
elif [ -f "main.py" ]; then
    APP_MODULE="main:app"
    echo "🚀 Starting FastAPI server (main.py)..."
else
    echo "❌ No main application file found!"
    echo "Expected: api/main.py or main.py"
    exit 1
fi

echo "📡 Server will be available at:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server
uvicorn $APP_MODULE --reload --host 0.0.0.0 --port 8000
