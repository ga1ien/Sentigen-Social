#!/bin/bash

# Complete Deployment Script
echo "🚀 Complete Deployment Pipeline"
echo "================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Deploy backend first
echo "📡 Step 1: Deploying Backend..."
bash "$SCRIPT_DIR/deploy-backend.sh"

if [ $? -ne 0 ]; then
    echo "❌ Backend deployment failed. Stopping deployment pipeline."
    exit 1
fi

echo ""
echo "✅ Backend deployed successfully!"
echo ""

# Wait a moment for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 10

# Test backend health
echo "🔍 Testing backend health..."
BACKEND_URL="https://sentigen-social-production.up.railway.app"
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")

if [ "$HEALTH_CHECK" = "200" ]; then
    echo "✅ Backend health check passed!"
else
    echo "⚠️ Backend health check failed (HTTP $HEALTH_CHECK), but continuing with frontend deployment..."
fi

echo ""

# Deploy frontend
echo "🌐 Step 2: Deploying Frontend..."
bash "$SCRIPT_DIR/deploy-frontend.sh"

if [ $? -ne 0 ]; then
    echo "❌ Frontend deployment failed."
    exit 1
fi

echo ""
echo "🎉 Complete deployment successful!"
echo "================================"
echo "🌐 Frontend: Check your Vercel dashboard"
echo "📡 Backend: $BACKEND_URL"
echo "📊 Health: $BACKEND_URL/health"
echo "📚 API Docs: $BACKEND_URL/docs"
echo "⚡ Performance: $BACKEND_URL/performance"
echo "================================"
