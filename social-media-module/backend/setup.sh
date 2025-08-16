#!/bin/bash
echo "🚀 Setting up Python environment per project standards..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    echo "Please install Python $REQUIRED_VERSION+ from https://python.org"
    exit 1
fi

echo "✅ Python version $PYTHON_VERSION meets requirements"

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "📦 Creating virtual environment 'venv' with Python $PYTHON_VERSION..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📦 Installing requirements..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "✅ All requirements installed successfully!"
    else
        echo "⚠️  Some packages may have failed to install. Check output above."
    fi
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Copy .env.example to .env and configure"
echo "  3. Start server: ./run.sh"
echo ""
echo "🔄 To activate this environment in the future:"
echo "  cd social-media-module/backend && source venv/bin/activate"
echo ""
echo "🛑 To deactivate:"
echo "  deactivate"
