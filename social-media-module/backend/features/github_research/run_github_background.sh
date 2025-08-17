#!/bin/bash

# GitHub Research Background Runner
# Manages background execution of GitHub scrapers and analyzers

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$BACKEND_DIR/venv"
LOGS_DIR="$BACKEND_DIR/logs"
PIDS_DIR="$SCRIPT_DIR/pids"

# Create necessary directories
mkdir -p "$LOGS_DIR" "$PIDS_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored messages
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️${NC} $1"
}

print_info() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')] 📊${NC} $1"
}

# Check if virtual environment exists
check_environment() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_info "Please run setup.sh first to create the virtual environment"
        exit 1
    fi

    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        print_error "Virtual environment activation script not found"
        exit 1
    fi
}

# Get PID file path for a scraper type
get_pid_file() {
    local scraper_type="$1"
    echo "$PIDS_DIR/github_${scraper_type}.pid"
}

# Get log file path for a scraper type
get_log_file() {
    local scraper_type="$1"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    echo "$LOGS_DIR/github_${scraper_type}_${timestamp}.log"
}

# Check if a scraper is running
is_running() {
    local scraper_type="$1"
    local pid_file=$(get_pid_file "$scraper_type")

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            # PID file exists but process is dead, clean up
            rm -f "$pid_file"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Stop a scraper
stop_scraper() {
    local scraper_type="$1"
    local pid_file=$(get_pid_file "$scraper_type")

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_status "Stopping GitHub $scraper_type scraper (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null

            # Wait for process to stop
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done

            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Force killing GitHub $scraper_type scraper..."
                kill -KILL "$pid" 2>/dev/null || true
            fi

            rm -f "$pid_file"
            print_success "GitHub $scraper_type scraper stopped"
        else
            print_warning "GitHub $scraper_type scraper PID file exists but process not running"
            rm -f "$pid_file"
        fi
    else
        print_warning "GitHub $scraper_type scraper is not running"
    fi
}

# Run raw data collection scraper
run_raw_scraper() {
    local scraper_type="raw"

    if is_running "$scraper_type"; then
        print_warning "GitHub raw scraper is already running"
        return 1
    fi

    local log_file=$(get_log_file "$scraper_type")
    local pid_file=$(get_pid_file "$scraper_type")

    print_status "Starting GitHub raw data collection scraper..."
    print_info "Log file: $log_file"
    print_info "PID file: $pid_file"

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    nohup python features/github_research/cli_github_scraper_raw.py \
        > "$log_file" 2>&1 &

    local pid=$!
    echo "$pid" > "$pid_file"

    # Wait a moment to see if it starts successfully
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "GitHub raw scraper started successfully (PID: $pid)"
        print_info "Monitor with: tail -f $log_file"
        return 0
    else
        print_error "GitHub raw scraper failed to start"
        rm -f "$pid_file"
        return 1
    fi
}

# Run AI analyzer
run_analyzer() {
    local scraper_type="analyzer"

    if is_running "$scraper_type"; then
        print_warning "GitHub analyzer is already running"
        return 1
    fi

    local log_file=$(get_log_file "$scraper_type")
    local pid_file=$(get_pid_file "$scraper_type")

    print_status "Starting GitHub AI analyzer..."
    print_info "Log file: $log_file"
    print_info "PID file: $pid_file"

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    nohup python features/github_research/cli_github_analyzer.py --latest \
        > "$log_file" 2>&1 &

    local pid=$!
    echo "$pid" > "$pid_file"

    # Wait a moment to see if it starts successfully
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "GitHub analyzer started successfully (PID: $pid)"
        print_info "Monitor with: tail -f $log_file"
        return 0
    else
        print_error "GitHub analyzer failed to start"
        rm -f "$pid_file"
        return 1
    fi
}

# Run complete pipeline (raw collection + analysis)
run_pipeline() {
    print_status "Starting GitHub complete pipeline..."

    # Stop any running processes first
    stop_scraper "raw"
    stop_scraper "analyzer"

    # Start raw collection
    if run_raw_scraper; then
        print_status "Waiting for raw collection to complete..."

        # Wait for raw scraper to finish
        local raw_pid_file=$(get_pid_file "raw")
        while [ -f "$raw_pid_file" ] && ps -p "$(cat "$raw_pid_file")" > /dev/null 2>&1; do
            sleep 10
            print_status "Raw collection still running..."
        done

        print_success "Raw collection completed, starting analysis..."

        # Start analyzer
        if run_analyzer; then
            print_success "GitHub pipeline started successfully"
            return 0
        else
            print_error "Failed to start analyzer"
            return 1
        fi
    else
        print_error "Failed to start raw collection"
        return 1
    fi
}

# Print status of all scrapers
print_status_all() {
    echo
    print_info "🔍 GITHUB RESEARCH STATUS"
    echo "=================================="

    local scrapers=("raw" "analyzer")
    local any_running=false

    for scraper in "${scrapers[@]}"; do
        if is_running "$scraper"; then
            local pid=$(cat "$(get_pid_file "$scraper")")
            print_success "GitHub $scraper: Running (PID: $pid)"
            any_running=true
        else
            print_error "GitHub $scraper: Not running"
        fi
    done

    if [ "$any_running" = false ]; then
        print_warning "No GitHub scrapers are currently running"
    fi

    echo
    print_info "📁 Data directories:"
    echo "   Raw data: $SCRIPT_DIR/raw_data"
    echo "   Analyzed data: $SCRIPT_DIR/analyzed_data"
    echo "   Logs: $LOGS_DIR"
    echo "   PIDs: $PIDS_DIR"
    echo

    # Check for GitHub token
    if [ -n "$GITHUB_TOKEN" ]; then
        print_info "🔑 GitHub token: Configured (5000 requests/hour)"
    else
        print_warning "🔑 GitHub token: Not configured (60 requests/hour limit)"
        print_info "   Set GITHUB_TOKEN environment variable for higher rate limits"
    fi
    echo
}

# Show usage
show_usage() {
    echo
    echo "🔍 GitHub Research Background Runner"
    echo "===================================="
    echo
    echo "Usage: $0 <command>"
    echo
    echo "Commands:"
    echo "  raw        - Start raw GitHub data collection"
    echo "  analyze    - Start AI analysis of latest raw data"
    echo "  pipeline   - Run complete pipeline (raw + analysis)"
    echo "  stop       - Stop all GitHub scrapers"
    echo "  status     - Show status of all scrapers"
    echo "  logs       - Show recent log entries"
    echo "  help       - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 raw                    # Start raw data collection"
    echo "  $0 analyze                # Analyze latest raw data"
    echo "  $0 pipeline               # Run complete pipeline"
    echo "  $0 status                 # Check what's running"
    echo "  $0 logs                   # View recent logs"
    echo
    echo "Environment Variables:"
    echo "  GITHUB_TOKEN              # GitHub personal access token (optional)"
    echo "                            # Without token: 60 requests/hour"
    echo "                            # With token: 5000 requests/hour"
    echo
    echo "To create a GitHub token:"
    echo "  1. Go to https://github.com/settings/tokens"
    echo "  2. Generate new token (classic)"
    echo "  3. Select 'public_repo' scope"
    echo "  4. Export GITHUB_TOKEN=your_token_here"
    echo
}

# Show recent logs
show_logs() {
    echo
    print_info "📋 Recent GitHub Research Logs"
    echo "==============================="

    # Find most recent log files
    local recent_logs=$(find "$LOGS_DIR" -name "github_*.log" -type f -mtime -1 | sort -r | head -5)

    if [ -z "$recent_logs" ]; then
        print_warning "No recent GitHub log files found"
        return
    fi

    for log_file in $recent_logs; do
        local basename=$(basename "$log_file")
        print_info "📄 $basename (last 10 lines):"
        echo "----------------------------------------"
        tail -10 "$log_file" 2>/dev/null || echo "Could not read log file"
        echo "----------------------------------------"
        echo
    done
}

# Main script logic
main() {
    # Check environment first
    check_environment

    case "${1:-help}" in
        "raw")
            run_raw_scraper
            ;;
        "analyze")
            run_analyzer
            ;;
        "pipeline")
            run_pipeline
            ;;
        "stop")
            print_status "Stopping all GitHub scrapers..."
            stop_scraper "raw"
            stop_scraper "analyzer"
            print_success "All GitHub scrapers stopped"
            ;;
        "status")
            print_status_all
            ;;
        "logs")
            show_logs
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
