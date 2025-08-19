#!/bin/bash

# Fix Railway Authentication Setup Script
# This script helps set up the required environment variables for authentication

set -e

echo "🔧 Fixing Railway Authentication Setup"
echo "=====================================\n"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
    echo "✅ Railway CLI installed"
fi

echo "🔑 Setting up authentication environment variables...\n"

# Check if user is logged in
if ! railway status &> /dev/null; then
    echo "🔐 Please log in to Railway:"
    railway login
fi

echo "📝 Setting critical environment variables..."

# Set the JWT secret (this is the key missing variable!)
echo "Setting JWT_SECRET..."
railway variables set JWT_SECRET="AMo8kf6/8Q8tBgpl4gBjQNuTJslL6/YMaSnnUWwdTXVggoAxCxFJeiKH2r3m0O+95xYfR1p6Q4IWfSRrl64yyg=="

# Set Supabase configuration
echo "Setting SUPABASE_URL..."
railway variables set SUPABASE_URL="https://lvgrswaemwvmjdawsvdj.supabase.co"

# Prompt for sensitive keys (don't hardcode these)
echo "\n🔐 Please provide your Supabase keys:"
echo "(Get these from: https://supabase.com/dashboard → Your Project → Settings → API)"

read -p "Enter SUPABASE_SERVICE_KEY (service_role key): " SUPABASE_SERVICE_KEY
if [[ -n "$SUPABASE_SERVICE_KEY" ]]; then
    railway variables set SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY"
    echo "✅ SUPABASE_SERVICE_KEY set"
else
    echo "⚠️ SUPABASE_SERVICE_KEY skipped"
fi

read -p "Enter SUPABASE_ANON_KEY (anon/public key): " SUPABASE_ANON_KEY
if [[ -n "$SUPABASE_ANON_KEY" ]]; then
    railway variables set SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY"
    echo "✅ SUPABASE_ANON_KEY set"
else
    echo "⚠️ SUPABASE_ANON_KEY skipped"
fi

# Set application environment
echo "\n🌍 Setting application environment..."
railway variables set APP_ENV="production"
railway variables set LOG_LEVEL="info"
railway variables set CORS_ORIGINS="https://zyyn.ai,https://www.zyyn.ai,http://localhost:3000"

echo "\n✅ Environment variables configured!"

# Check if we should redeploy
read -p "🚀 Deploy now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying..."
    railway up --detach
    echo "\n🎉 Deployment started! Check Railway dashboard for progress."
    echo "🔍 Monitor logs: railway logs --follow"
else
    echo "⏭️ Skipping deployment. Run 'railway up' when ready."
fi

echo "\n📋 Next steps:"
echo "1. Wait for deployment to complete"
echo "2. Check logs: railway logs --follow"
echo "3. Look for: 'JWT_SECRET loaded from environment'"
echo "4. Test health endpoint: curl https://your-app.up.railway.app/health"
echo "5. Test authentication from the frontend"

echo "\n🧪 To test JWT validation locally:"
echo "cd social-media-module/backend"
echo "export JWT_SECRET='AMo8kf6/8Q8tBgpl4gBjQNuTJslL6/YMaSnnUWwdTXVggoAxCxFJeiKH2r3m0O+95xYfR1p6Q4IWfSRrl64yyg=='"
echo "python test_jwt_validation.py"

echo "\n✨ Authentication should now work!"
