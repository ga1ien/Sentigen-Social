#!/bin/bash
#
# Reddit Research Background Scraper
# Runs the Reddit CLI scraper in the background on macOS terminal
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
VENV_PATH="$BACKEND_DIR/venv"
CLI_SCRIPT="$BACKEND_DIR/features/reddit_research/cli_reddit_scraper.py"
LOG_DIR="$BACKEND_DIR/logs"
PID_FILE="$LOG_DIR/reddit_scraper.pid"

# Create logs directory
mkdir -p "$LOG_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $1"
}

# Function to check if scraper is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the scraper
start_scraper() {
    print_status "Starting Reddit Research Scraper..."

    # Check if already running
    if is_running; then
        print_warning "Scraper is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_status "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi

    # Check if CLI script exists
    if [ ! -f "$CLI_SCRIPT" ]; then
        print_error "CLI script not found at $CLI_SCRIPT"
        return 1
    fi

    # Activate virtual environment and run scraper in background
    print_status "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"

    print_status "Starting scraper in background..."

    # Run the scraper with nohup to keep it running after terminal closes
    nohup python "$CLI_SCRIPT" \
        --query "AI automation tools business productivity" \
        --subreddits artificial productivity Entrepreneur SaaS \
        --max-posts 15 \
        --name "Background CLI Research $(date '+%Y-%m-%d %H:%M')" \
        > "$LOG_DIR/reddit_scraper.log" 2>&1 &

    # Save PID
    local pid=$!
    echo "$pid" > "$PID_FILE"

    print_success "Reddit scraper started in background (PID: $pid)"
    print_status "Logs: $LOG_DIR/reddit_scraper.log"
    print_status "PID file: $PID_FILE"

    # Wait a moment and check if it's still running
    sleep 3
    if is_running; then
        print_success "Scraper is running successfully"
        print_status "Use './run_reddit_scraper.sh status' to check progress"
        print_status "Use './run_reddit_scraper.sh stop' to stop the scraper"
        print_status "Use './run_reddit_scraper.sh logs' to view logs"
    else
        print_error "Scraper failed to start. Check logs for details."
        return 1
    fi
}

# Function to stop the scraper
stop_scraper() {
    print_status "Stopping Reddit Research Scraper..."

    if ! is_running; then
        print_warning "Scraper is not running"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    print_status "Sending SIGTERM to process $pid..."

    kill "$pid" 2>/dev/null

    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
    done

    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "Graceful shutdown failed, force killing..."
        kill -9 "$pid" 2>/dev/null
    fi

    rm -f "$PID_FILE"
    print_success "Reddit scraper stopped"
}

# Function to show status
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_success "Reddit scraper is running (PID: $pid)"

        # Show process info
        print_status "Process info:"
        ps -p "$pid" -o pid,ppid,etime,pcpu,pmem,cmd

        # Show recent logs
        if [ -f "$LOG_DIR/reddit_scraper.log" ]; then
            print_status "Recent logs (last 10 lines):"
            tail -10 "$LOG_DIR/reddit_scraper.log"
        fi
    else
        print_warning "Reddit scraper is not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_DIR/reddit_scraper.log" ]; then
        print_status "Showing Reddit scraper logs (press Ctrl+C to exit):"
        tail -f "$LOG_DIR/reddit_scraper.log"
    else
        print_error "Log file not found: $LOG_DIR/reddit_scraper.log"
    fi
}

# Function to show help
show_help() {
    echo "Reddit Research Background Scraper"
    echo "=================================="
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the Reddit scraper in background"
    echo "  stop     - Stop the running scraper"
    echo "  restart  - Restart the scraper"
    echo "  status   - Show scraper status and recent logs"
    echo "  logs     - Follow the scraper logs in real-time"
    echo "  help     - Show this help message"
    echo ""
    echo "Files:"
    echo "  Logs: $LOG_DIR/reddit_scraper.log"
    echo "  PID:  $PID_FILE"
    echo "  CLI:  $CLI_SCRIPT"
    echo ""
    echo "Examples:"
    echo "  ./run_reddit_scraper.sh start"
    echo "  ./run_reddit_scraper.sh status"
    echo "  ./run_reddit_scraper.sh logs"
    echo "  ./run_reddit_scraper.sh stop"
}

# Main script logic
case "${1:-help}" in
    start)
        start_scraper
        ;;
    stop)
        stop_scraper
        ;;
    restart)
        stop_scraper
        sleep 2
        start_scraper
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
