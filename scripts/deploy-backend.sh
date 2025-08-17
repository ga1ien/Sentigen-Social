#!/bin/bash

# Backend Deployment Script for Railway
echo "🚀 Deploying Backend to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")/../social-media-module/backend" || exit 1

echo "📂 Current directory: $(pwd)"

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway first:"
    railway login
fi

# Validate environment variables
echo "🔍 Validating environment configuration..."
python scripts/validate_config.py

if [ $? -ne 0 ]; then
    echo "❌ Environment validation failed. Please check your configuration."
    exit 1
fi

# Run tests before deployment
echo "🧪 Running API tests..."
./scripts/quick_api_test.sh

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway up

if [ $? -eq 0 ]; then
    echo "✅ Backend deployment successful!"
    echo "🌐 Your API is now live at: https://sentigen-social-production.up.railway.app"
    echo "📊 Health check: https://sentigen-social-production.up.railway.app/health"
    echo "📚 API docs: https://sentigen-social-production.up.railway.app/docs"
else
    echo "❌ Deployment failed. Check Railway logs for details."
    exit 1
fi
