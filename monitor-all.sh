#!/bin/bash

# Comprehensive Real-time Monitoring CLI for Sentigen Social
# Shows Vercel, Railway, Git, and System status in real-time

# Colors for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored headers
print_header() {
    echo -e "${WHITE}================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${WHITE}================================${NC}"
}

print_section() {
    echo -e "${CYAN}--- $1 ---${NC}"
}

# Function to check command availability
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 not found${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $1 available${NC}"
        return 0
    fi
}

# Function to get git status
get_git_status() {
    print_section "Git Status"
    
    # Current branch
    branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    echo -e "${BLUE}Branch:${NC} $branch"
    
    # Uncommitted changes
    if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
        echo -e "${YELLOW}📝 Uncommitted changes:${NC}"
        git status --short 2>/dev/null | head -10
    else
        echo -e "${GREEN}✅ Working directory clean${NC}"
    fi
    
    # Last commit
    echo -e "${BLUE}Last commit:${NC}"
    git log -1 --oneline 2>/dev/null || echo "No commits found"
    
    # Remote status
    echo -e "${BLUE}Remote status:${NC}"
    git status -b --porcelain=v1 2>/dev/null | head -1 || echo "No remote configured"
}

# Function to get Vercel status
get_vercel_status() {
    print_section "Vercel Status"
    
    if check_command "vercel"; then
        echo -e "${BLUE}Project info:${NC}"
        vercel project ls 2>/dev/null | grep -E "(sentigen|Sentigen)" || echo "No projects found"
        
        echo -e "${BLUE}Recent deployments:${NC}"
        vercel list --limit 3 2>/dev/null || echo "No deployments found"
        
        echo -e "${BLUE}Current deployment status:${NC}"
        vercel inspect --wait 2>/dev/null || echo "No active deployment"
    fi
}

# Function to get Railway status
get_railway_status() {
    print_section "Railway Status"
    
    if check_command "railway"; then
        echo -e "${BLUE}Project info:${NC}"
        railway status 2>/dev/null || echo "Not connected to Railway project"
        
        echo -e "${BLUE}Recent deployments:${NC}"
        railway logs --limit 5 2>/dev/null || echo "No logs available"
        
        echo -e "${BLUE}Service health:${NC}"
        curl -s -o /dev/null -w "Status: %{http_code} | Time: %{time_total}s" \
            https://sentigen-social-production.up.railway.app/health 2>/dev/null || echo "Service unreachable"
        echo ""
    fi
}

# Function to get system status
get_system_status() {
    print_section "System Status"
    
    echo -e "${BLUE}Current time:${NC} $(date)"
    echo -e "${BLUE}Uptime:${NC} $(uptime | awk '{print $3,$4}' | sed 's/,//')"
    
    # Memory usage
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo -e "${BLUE}Memory:${NC} $(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')KB free"
    else
        # Linux
        echo -e "${BLUE}Memory:${NC} $(free -h | grep Mem | awk '{print $3"/"$2}')"
    fi
    
    # Disk usage
    echo -e "${BLUE}Disk usage:${NC} $(df -h . | tail -1 | awk '{print $3"/"$2" ("$5" used)"}')"
    
    # Network connectivity
    echo -e "${BLUE}Network:${NC}"
    if ping -c 1 google.com &> /dev/null; then
        echo -e "${GREEN}✅ Internet connected${NC}"
    else
        echo -e "${RED}❌ No internet connection${NC}"
    fi
}

# Function to get process status
get_process_status() {
    print_section "Development Processes"
    
    # Check for common development processes
    processes=("node" "npm" "next" "python" "uvicorn" "railway" "vercel")
    
    for proc in "${processes[@]}"; do
        count=$(pgrep -f "$proc" | wc -l | tr -d ' ')
        if [[ $count -gt 0 ]]; then
            echo -e "${GREEN}✅ $proc: $count process(es) running${NC}"
        else
            echo -e "${YELLOW}⚪ $proc: not running${NC}"
        fi
    done
}

# Function to monitor logs in real-time
monitor_logs() {
    print_section "Live Logs"
    
    echo -e "${BLUE}Monitoring logs... (Press Ctrl+C to stop)${NC}"
    
    # Try to tail various log files
    if [[ -f "frontend/.next/trace" ]]; then
        echo -e "${CYAN}Next.js trace:${NC}"
        tail -f frontend/.next/trace &
    fi
    
    # Monitor Railway logs if available
    if command -v railway &> /dev/null; then
        echo -e "${CYAN}Railway logs:${NC}"
        railway logs --follow &
    fi
    
    # Monitor Vercel logs if available
    if command -v vercel &> /dev/null; then
        echo -e "${CYAN}Vercel logs:${NC}"
        vercel logs --follow &
    fi
    
    wait
}

# Main monitoring function
run_monitor() {
    while true; do
        clear
        print_header "🚀 SENTIGEN SOCIAL - REAL-TIME MONITOR"
        echo -e "${WHITE}$(date)${NC}"
        echo ""
        
        get_git_status
        echo ""
        
        get_vercel_status
        echo ""
        
        get_railway_status
        echo ""
        
        get_system_status
        echo ""
        
        get_process_status
        echo ""
        
        echo -e "${WHITE}Press Ctrl+C to exit | Refreshing in 10 seconds...${NC}"
        echo -e "${YELLOW}Commands: [c]ommit [p]ush [d]eploy [l]ogs [q]uit${NC}"
        
        # Wait for 10 seconds or user input
        read -t 10 -n 1 input
        
        case $input in
            c|C)
                echo ""
                echo -e "${CYAN}Committing changes...${NC}"
                git add .
                git commit -m "feat: auto-commit via monitor $(date)"
                ;;
            p|P)
                echo ""
                echo -e "${CYAN}Pushing to GitHub...${NC}"
                git push origin main
                ;;
            d|D)
                echo ""
                echo -e "${CYAN}Deploying to Railway...${NC}"
                cd social-media-module/backend && railway deploy
                cd ../..
                ;;
            l|L)
                monitor_logs
                ;;
            q|Q)
                echo ""
                echo -e "${GREEN}Monitor stopped.${NC}"
                exit 0
                ;;
        esac
    done
}

# Check if running with specific command
case "$1" in
    "logs")
        monitor_logs
        ;;
    "status")
        get_git_status
        echo ""
        get_vercel_status
        echo ""
        get_railway_status
        echo ""
        get_system_status
        ;;
    "git")
        get_git_status
        ;;
    "vercel")
        get_vercel_status
        ;;
    "railway")
        get_railway_status
        ;;
    *)
        echo -e "${WHITE}🚀 Starting Sentigen Social Monitor...${NC}"
        echo -e "${CYAN}Usage: $0 [logs|status|git|vercel|railway]${NC}"
        echo -e "${CYAN}Running full monitor in 3 seconds...${NC}"
        sleep 3
        run_monitor
        ;;
esac
