#!/bin/bash

# Frontend Deployment Script for Vercel
echo "🚀 Deploying Frontend to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Please install it first:"
    echo "   npm install -g vercel"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

echo "📂 Current directory: $(pwd)"

# Check if logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please login to Vercel first:"
    vercel login
fi

# Navigate to frontend and build
echo "🔨 Building frontend..."
cd frontend || exit 1

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Run build to check for errors
echo "🏗️ Running production build..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed. Please fix errors before deploying."
    exit 1
fi

# Go back to project root for deployment
cd ..

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

if [ $? -eq 0 ]; then
    echo "✅ Frontend deployment successful!"
    echo "🌐 Your app is now live!"
    echo "📱 Check your Vercel dashboard for the live URL"
else
    echo "❌ Deployment failed. Check Vercel logs for details."
    exit 1
fi
