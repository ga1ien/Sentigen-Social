#!/bin/bash

# AI Social Media Platform - Development Server Startup Script

echo "🚀 Starting AI Social Media Platform Development Servers..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port $1 is already in use${NC}"
        return 1
    else
        return 0
    fi
}

# Check if required directories exist
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Frontend directory not found${NC}"
    exit 1
fi

if [ ! -d "social-media-module/backend" ]; then
    echo -e "${RED}❌ Backend directory not found${NC}"
    exit 1
fi

# Start Frontend (Next.js)
echo -e "${BLUE}📱 Starting Frontend (Next.js)...${NC}"
if check_port 3000; then
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ Frontend started on http://localhost:3000 (PID: $FRONTEND_PID)${NC}"
    cd ..
else
    echo -e "${YELLOW}Frontend may already be running on port 3000${NC}"
fi

# Wait a moment
sleep 2

# Start Backend (FastAPI)
echo -e "${BLUE}⚡ Starting Backend (FastAPI)...${NC}"
if check_port 8000; then
    cd social-media-module/backend
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        echo -e "${GREEN}🐍 Activating Python virtual environment...${NC}"
        source venv/bin/activate
    fi
    
    # Start FastAPI with uvicorn
    python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend started on http://localhost:8000 (PID: $BACKEND_PID)${NC}"
    echo -e "${GREEN}📚 API Documentation: http://localhost:8000/docs${NC}"
    cd ../..
else
    echo -e "${YELLOW}Backend may already be running on port 8000${NC}"
fi

# Wait a moment
sleep 2

# Check Chrome MCP
echo -e "${BLUE}🧠 Checking Chrome MCP Server...${NC}"
if check_port 12306; then
    echo -e "${YELLOW}Chrome MCP Server not running. Start it manually with:${NC}"
    echo -e "${YELLOW}mcp-chrome-bridge register${NC}"
else
    echo -e "${GREEN}✅ Chrome MCP Server is running on http://127.0.0.1:12306${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Development Environment Ready!${NC}"
echo ""
echo -e "${BLUE}📱 Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}⚡ Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}🔍 Health Check:${NC} http://localhost:8000/health"
echo -e "${BLUE}🧠 Chrome MCP:${NC} http://127.0.0.1:12306"
echo ""
echo -e "${YELLOW}💡 Pro Tip: Open these URLs in separate browser tabs for the best development experience!${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop all servers${NC}"

# Keep script running and handle Ctrl+C
trap 'echo -e "\n${YELLOW}🛑 Stopping all servers...${NC}"; kill $FRONTEND_PID $BACKEND_PID 2>/dev/null; exit' INT

# Wait for user input
wait
