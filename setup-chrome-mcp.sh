#!/bin/bash

# Define colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}--- Setting up Chrome MCP Server ---${NC}"

# 1. Check if Chrome MCP bridge is installed
echo -e "\n${YELLOW}1. Checking Chrome MCP bridge installation...${NC}"
if command -v mcp-chrome-bridge &> /dev/null; then
    echo -e "${GREEN}✅ Chrome MCP bridge is installed${NC}"
else
    echo -e "${RED}❌ Chrome MCP bridge not found. Installing...${NC}"
    npm install -g mcp-chrome-bridge
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Chrome MCP bridge installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install Chrome MCP bridge${NC}"
        exit 1
    fi
fi

# 2. Check Chrome extension directory
echo -e "\n${YELLOW}2. Checking Chrome extension...${NC}"
EXTENSION_DIR="/Users/galenoakes/Development/chrome-mcp-extension"
if [ -d "$EXTENSION_DIR" ]; then
    echo -e "${GREEN}✅ Chrome extension directory found: $EXTENSION_DIR${NC}"
    echo -e "${BLUE}Extension contents:${NC}"
    ls -la "$EXTENSION_DIR" | head -10
else
    echo -e "${RED}❌ Chrome extension directory not found${NC}"
    exit 1
fi

# 3. Start Chrome MCP bridge server
echo -e "\n${YELLOW}3. Starting Chrome MCP bridge server...${NC}"
echo -e "${BLUE}Starting server on http://127.0.0.1:12306/mcp${NC}"

# Check if server is already running
if lsof -i :12306 | grep LISTEN > /dev/null; then
    echo -e "${YELLOW}⚠️ Server already running on port 12306${NC}"
    echo -e "${GREEN}Chrome MCP server is ready!${NC}"
else
    echo -e "${BLUE}Starting new Chrome MCP server...${NC}"
    mcp-chrome-bridge &
    SERVER_PID=$!
    echo -e "${GREEN}Chrome MCP server started with PID: $SERVER_PID${NC}"

    # Wait for server to be ready
    echo -e "${YELLOW}Waiting for server to be ready...${NC}"
    timeout 30 bash -c '
        while ! curl -s http://127.0.0.1:12306/mcp > /dev/null; do
            sleep 1
        done
    '

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Chrome MCP server is ready!${NC}"
    else
        echo -e "${RED}❌ Server did not start within timeout${NC}"
        kill $SERVER_PID 2>/dev/null
        exit 1
    fi
fi

# 4. Instructions for Chrome extension
echo -e "\n${BLUE}--- Chrome Extension Setup Instructions ---${NC}"
echo -e "${YELLOW}To complete the setup:${NC}"
echo -e "1. Open Chrome and go to: ${BLUE}chrome://extensions/${NC}"
echo -e "2. Enable '${YELLOW}Developer mode${NC}' (toggle in top right)"
echo -e "3. Click '${YELLOW}Load unpacked${NC}'"
echo -e "4. Select this folder: ${BLUE}$EXTENSION_DIR${NC}"
echo -e "5. Click the extension icon in Chrome toolbar"
echo -e "6. Click '${YELLOW}Connect${NC}' to connect to the MCP server"

# 5. Test connection
echo -e "\n${YELLOW}5. Testing MCP server connection...${NC}"
response=$(curl -s -w "%{http_code}" http://127.0.0.1:12306/mcp)
http_code="${response: -3}"

if [ "$http_code" == "200" ] || [ "$http_code" == "404" ]; then
    echo -e "${GREEN}✅ MCP server is responding (Status: $http_code)${NC}"
else
    echo -e "${RED}❌ MCP server connection failed (Status: $http_code)${NC}"
fi

echo -e "\n${BLUE}--- Setup Complete ---${NC}"
echo -e "${GREEN}Chrome MCP Server: http://127.0.0.1:12306/mcp${NC}"
echo -e "${GREEN}Extension Directory: $EXTENSION_DIR${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Install the Chrome extension (see instructions above)"
echo -e "2. Test the research workflow at: ${BLUE}http://localhost:3000/dashboard/research-video${NC}"
echo -e "3. The system can now open multiple Chrome tabs for research on Reddit, LinkedIn, Substack, etc."

echo -e "\n${BLUE}Keep this terminal open to keep the MCP server running.${NC}"
