#!/bin/bash

# Local Testing Setup Script for Sentigen Social
# Starts all services and runs comprehensive tests

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${WHITE}================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${WHITE}================================${NC}"
}

print_step() {
    echo -e "${CYAN}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    print_step "Waiting for $name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$name is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "$name failed to start after $max_attempts attempts"
    return 1
}

# Main setup function
main() {
    clear
    print_header "🚀 SENTIGEN SOCIAL - LOCAL TESTING SETUP"

    # Check if we're in the right directory
    if [ ! -f "package.json" ] && [ ! -d "frontend" ]; then
        print_error "Please run this script from the Sentigen-Social root directory"
        exit 1
    fi

    print_step "Checking system requirements..."

    # Check Node.js
    if command -v node &> /dev/null; then
        node_version=$(node --version)
        print_success "Node.js $node_version installed"
    else
        print_error "Node.js not found. Please install Node.js"
        exit 1
    fi

    # Check npm
    if command -v npm &> /dev/null; then
        npm_version=$(npm --version)
        print_success "npm $npm_version installed"
    else
        print_error "npm not found"
        exit 1
    fi

    print_step "Installing frontend dependencies..."
    cd frontend
    npm install
    if [ $? -eq 0 ]; then
        print_success "Frontend dependencies installed"
    else
        print_error "Failed to install frontend dependencies"
        exit 1
    fi
    cd ..

    print_step "Checking backend status..."
    backend_url="https://sentigen-social-production.up.railway.app"
    if curl -s "$backend_url/health" > /dev/null; then
        print_success "Backend is live on Railway"
    else
        print_warning "Backend may not be responding. Check Railway deployment."
    fi

    print_step "Starting frontend development server..."

    # Kill any existing processes on port 3000
    if check_port 3000; then
        print_warning "Port 3000 is in use. Killing existing process..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # Start frontend in background
    cd frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..

    # Wait for frontend to be ready
    if wait_for_service "http://localhost:3000" "Frontend"; then
        print_success "Frontend is running on http://localhost:3000"
    else
        print_error "Frontend failed to start. Check frontend.log for details."
        kill $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi

    print_step "Running connectivity tests..."

    # Test frontend
    if curl -s "http://localhost:3000" | grep -q "html"; then
        print_success "Frontend responding correctly"
    else
        print_error "Frontend not responding correctly"
    fi

    # Test backend
    backend_health=$(curl -s "$backend_url/health" | jq -r '.status' 2>/dev/null || echo "error")
    if [ "$backend_health" = "healthy" ]; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check failed or returned: $backend_health"
    fi

    # Test API endpoints
    print_step "Testing Research-to-Video API endpoints..."

    # Test research endpoint
    research_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$backend_url/api/research-video/start" \
        -H "Content-Type: application/json" \
        -d '{"research_topics":["test"],"target_audience":"developers","video_style":"professional"}')

    if [ "$research_response" = "200" ] || [ "$research_response" = "422" ]; then
        print_success "Research API endpoint responding (HTTP $research_response)"
    else
        print_warning "Research API endpoint returned HTTP $research_response"
    fi

    print_header "🎉 LOCAL TESTING ENVIRONMENT READY!"

    echo -e "${WHITE}Frontend:${NC} http://localhost:3000"
    echo -e "${WHITE}Backend:${NC} $backend_url"
    echo -e "${WHITE}Research-to-Video:${NC} http://localhost:3000/dashboard/research-video"
    echo -e "${WHITE}AI Avatars:${NC} http://localhost:3000/dashboard/avatars"
    echo ""

    echo -e "${CYAN}📋 Testing Checklist:${NC}"
    echo -e "${WHITE}1.${NC} Navigate to http://localhost:3000/dashboard/research-video"
    echo -e "${WHITE}2.${NC} Add research topics (e.g., 'AI automation', 'productivity tools')"
    echo -e "${WHITE}3.${NC} Set target audience (e.g., 'tech entrepreneurs')"
    echo -e "${WHITE}4.${NC} Click 'Start Research' and watch the progress"
    echo -e "${WHITE}5.${NC} Review generated insights and trending topics"
    echo -e "${WHITE}6.${NC} Generate and approve the AI script"
    echo -e "${WHITE}7.${NC} Select an avatar for video generation"
    echo -e "${WHITE}8.${NC} Preview and approve the generated video"
    echo -e "${WHITE}9.${NC} Publish to TikTok, IG Reels, YouTube Shorts"
    echo ""

    echo -e "${YELLOW}📊 Monitoring:${NC}"
    echo -e "${WHITE}• Run${NC} ./monitor-all.sh ${WHITE}for real-time monitoring${NC}"
    echo -e "${WHITE}• Check${NC} frontend.log ${WHITE}for frontend logs${NC}"
    echo -e "${WHITE}• Use${NC} curl $backend_url/health ${WHITE}to check backend${NC}"
    echo ""

    echo -e "${GREEN}🚀 Ready to test! Press Ctrl+C to stop all services.${NC}"

    # Keep script running and monitor
    trap 'echo -e "\n${YELLOW}Stopping services...${NC}"; kill $FRONTEND_PID 2>/dev/null || true; exit 0' INT

    # Monitor services
    while true; do
        sleep 10
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died. Restarting..."
            cd frontend
            npm run dev > ../frontend.log 2>&1 &
            FRONTEND_PID=$!
            cd ..
        fi
    done
}

# Run main function
main "$@"
