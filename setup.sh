#!/bin/bash

# AI Social Media Platform - Setup Script
# This script helps you set up the development environment

set -e

echo "🚀 AI Social Media Platform Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if required tools are installed
check_requirements() {
    print_info "Checking system requirements..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/"
        exit 1
    fi

    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node -v)"
        exit 1
    fi
    print_status "Node.js $(node -v) is installed"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+ from https://python.org/"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python $PYTHON_VERSION is installed"

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm."
        exit 1
    fi
    print_status "npm $(npm -v) is installed"

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip3."
        exit 1
    fi
    print_status "pip3 is installed"
}

# Setup environment files
setup_environment() {
    print_info "Setting up environment files..."

    # Check if unified template exists
    if [ ! -f "env.unified.template" ]; then
        print_error "env.unified.template not found!"
        exit 1
    fi

    # Main environment file
    if [ ! -f ".env" ]; then
        cp env.unified.template .env
        print_status "Created .env from unified template"
        print_warning "Please edit .env with your actual configuration values"
        print_info "See docs/ENVIRONMENT_SETUP.md for detailed instructions"
    else
        print_warning ".env already exists"
    fi

    # Frontend environment (extract NEXT_PUBLIC_* variables)
    if [ ! -f "frontend/.env.local" ]; then
        grep "^NEXT_PUBLIC_" env.unified.template > frontend/.env.local
        print_status "Created frontend/.env.local with NEXT_PUBLIC_* variables"
        print_warning "Update frontend/.env.local with your actual values"
    else
        print_warning "frontend/.env.local already exists"
    fi
}

# Install frontend dependencies
setup_frontend() {
    print_info "Setting up frontend..."

    cd frontend

    print_info "Installing frontend dependencies..."
    npm install
    print_status "Frontend dependencies installed"

    cd ..
}

# Install backend dependencies
setup_backend() {
    print_info "Setting up backend..."

    cd social-media-module/backend

    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_status "Virtual environment created"
    fi

    # Activate virtual environment and install dependencies
    print_info "Installing backend dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    print_status "Backend dependencies installed"

    cd ../..
}

# Test installations
test_setup() {
    print_info "Testing setup..."

    # Test frontend
    cd frontend
    if npm run build > /dev/null 2>&1; then
        print_status "Frontend build test passed"
    else
        print_warning "Frontend build test failed - check your configuration"
    fi
    cd ..

    # Test backend
    cd social-media-module/backend
    source venv/bin/activate
    if python -c "import fastapi, pydantic_ai, supabase" > /dev/null 2>&1; then
        print_status "Backend import test passed"
    else
        print_warning "Backend import test failed - check your dependencies"
    fi
    cd ../..
}

# Main setup function
main() {
    echo
    print_info "Starting setup process..."
    echo

    check_requirements
    echo

    setup_environment
    echo

    setup_frontend
    echo

    setup_backend
    echo

    test_setup
    echo

    print_status "Setup completed successfully!"
    echo
    print_info "Next steps:"
    echo "1. Configure your environment:"
    echo "   - Edit .env with your API keys and configuration"
    echo "   - Update frontend/.env.local with NEXT_PUBLIC_* variables"
    echo "   - See docs/ENVIRONMENT_SETUP.md for detailed instructions"
    echo
    echo "2. Validate your configuration:"
    echo "   python3 scripts/validate_environment.py"
    echo
    echo "3. Set up your Supabase database:"
    echo "   - Create a new Supabase project"
    echo "   - Run: psql -d \"your-supabase-connection-string\" -f database/master_database_schema.sql"
    echo
    echo "4. Start the development servers:"
    echo "   Frontend: cd frontend && npm run dev"
    echo "   Backend:  cd social-media-module/backend && source venv/bin/activate && python -m uvicorn api.main:app --reload"
    echo
    echo "5. Access the application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo
    print_status "Happy coding! 🎉"
}

# Run main function
main
