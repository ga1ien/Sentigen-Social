#!/bin/bash

# Social Media Module Setup Script
echo "🚀 Setting up Social Media Module..."

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the social-media-module directory"
    exit 1
fi

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your API keys!"
else
    echo "✅ .env file already exists"
fi

cd ..

# Frontend setup
echo "📦 Setting up frontend..."
cd frontend

# Install Node.js dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
else
    echo "✅ Node.js dependencies already installed"
fi

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit backend/.env with your API keys:"
echo "   - AYRSHARE_API_KEY (already set)"
echo "   - OPENAI_API_KEY"
echo "   - ANTHROPIC_API_KEY (optional)"
echo "   - HEYGEN_API_KEY (optional)"
echo "   - PERPLEXITY_API_KEY (optional)"
echo ""
echo "2. Start the backend:"
echo "   cd backend && source venv/bin/activate && python main.py"
echo ""
echo "3. Start the frontend (in a new terminal):"
echo "   cd frontend && npm start"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "❤️  Happy posting!"