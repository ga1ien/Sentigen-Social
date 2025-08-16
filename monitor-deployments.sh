#!/bin/bash

# Deployment Monitor Script
# Usage: ./monitor-deployments.sh

echo "🚀 Sentigen-Social Deployment Monitor"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists "gh"; then
    echo -e "${RED}❌ GitHub CLI not found. Install with: brew install gh${NC}"
    exit 1
fi

if ! command_exists "railway"; then
    echo -e "${RED}❌ Railway CLI not found. Install with: npm install -g @railway/cli${NC}"
    exit 1
fi

if ! command_exists "vercel"; then
    echo -e "${RED}❌ Vercel CLI not found. Install with: npm install -g vercel${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All CLIs installed${NC}"
echo ""

# Function to monitor Railway deployment
monitor_railway() {
    echo -e "${BLUE}🚂 Railway Backend Status:${NC}"
    echo "------------------------"
    
    cd social-media-module/backend
    
    # Get Railway status
    railway status 2>/dev/null || echo -e "${RED}❌ Not connected to Railway project${NC}"
    
    echo ""
    echo -e "${YELLOW}📊 Recent Railway logs:${NC}"
    railway logs --tail 10 2>/dev/null || echo -e "${RED}❌ Cannot fetch logs${NC}"
    
    echo ""
    echo -e "${YELLOW}🔗 Railway URLs:${NC}"
    railway domain 2>/dev/null || echo -e "${RED}❌ No domains configured${NC}"
    
    cd ../..
}

# Function to monitor Vercel deployment
monitor_vercel() {
    echo -e "${BLUE}▲ Vercel Frontend Status:${NC}"
    echo "-------------------------"
    
    cd frontend
    
    # Get Vercel deployments
    echo -e "${YELLOW}📊 Recent Vercel deployments:${NC}"
    vercel ls --scope team_sentigen 2>/dev/null || vercel ls 2>/dev/null || echo -e "${RED}❌ Cannot fetch deployments${NC}"
    
    echo ""
    echo -e "${YELLOW}🔗 Production URL:${NC}"
    vercel inspect --scope team_sentigen 2>/dev/null || echo -e "${RED}❌ No production deployment found${NC}"
    
    cd ..
}

# Function to check GitHub status
monitor_github() {
    echo -e "${BLUE}🐙 GitHub Repository Status:${NC}"
    echo "----------------------------"
    
    echo -e "${YELLOW}📊 Recent commits:${NC}"
    gh repo view --json name,url,pushedAt,defaultBranchRef 2>/dev/null || echo -e "${RED}❌ Cannot fetch repo info${NC}"
    
    echo ""
    echo -e "${YELLOW}🔄 Recent workflow runs:${NC}"
    gh run list --limit 5 2>/dev/null || echo -e "${RED}❌ No workflow runs found${NC}"
}

# Function to test endpoints
test_endpoints() {
    echo -e "${BLUE}🧪 Testing Endpoints:${NC}"
    echo "--------------------"
    
    # Test Railway backend
    echo -e "${YELLOW}Testing Railway backend...${NC}"
    RAILWAY_URL=$(cd social-media-module/backend && railway domain 2>/dev/null | head -1)
    if [ ! -z "$RAILWAY_URL" ]; then
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/health" || echo "000")
        if [ "$HTTP_STATUS" = "200" ]; then
            echo -e "${GREEN}✅ Backend health check: OK${NC}"
        else
            echo -e "${RED}❌ Backend health check: Failed ($HTTP_STATUS)${NC}"
        fi
    else
        echo -e "${RED}❌ Cannot determine Railway URL${NC}"
    fi
    
    # Test Vercel frontend
    echo -e "${YELLOW}Testing Vercel frontend...${NC}"
    VERCEL_URL=$(cd frontend && vercel inspect --scope team_sentigen 2>/dev/null | grep -o 'https://[^"]*' | head -1)
    if [ ! -z "$VERCEL_URL" ]; then
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$VERCEL_URL" || echo "000")
        if [ "$HTTP_STATUS" = "200" ]; then
            echo -e "${GREEN}✅ Frontend: OK${NC}"
        else
            echo -e "${RED}❌ Frontend: Failed ($HTTP_STATUS)${NC}"
        fi
    else
        echo -e "${RED}❌ Cannot determine Vercel URL${NC}"
    fi
}

# Main monitoring loop
while true; do
    clear
    echo "🚀 Sentigen-Social Deployment Monitor - $(date)"
    echo "================================================"
    echo ""
    
    monitor_github
    echo ""
    monitor_railway
    echo ""
    monitor_vercel
    echo ""
    test_endpoints
    echo ""
    
    echo -e "${BLUE}Press Ctrl+C to exit, or wait 30 seconds for refresh...${NC}"
    sleep 30
done
