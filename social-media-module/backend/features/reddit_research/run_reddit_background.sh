#!/bin/bash
#
# Reddit Research Background Runner
# Runs Reddit scrapers in background so you can continue using Cursor
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="/Users/galenoakes/Development/Sentigen-Social/social-media-module/backend"
VENV_PATH="$PROJECT_DIR/venv"
LOGS_DIR="$PROJECT_DIR/logs"
RESULTS_DIR="$PROJECT_DIR/features/reddit_research/results"

# Create directories
mkdir -p "$LOGS_DIR"
mkdir -p "$RESULTS_DIR"

# Function to print colored output
print_header() {
    echo -e "${PURPLE}🤖 Reddit Research Background Runner${NC}"
    echo -e "${PURPLE}====================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}📝 $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show usage
show_usage() {
    print_header
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  simple              Run simple Reddit scraper (default settings)"
    echo "  streaming           Run streaming scraper with real-time output"
    echo "  raw                 Run raw data collection (fast, no AI analysis)"
    echo "  analyze             Run AI analysis on collected raw data"
    echo "  pipeline            Run full pipeline (raw collection + analysis)"
    echo "  configurable        Run configurable scraper with custom options"
    echo "  custom              Run with custom parameters"
    echo "  status              Check running background processes"
    echo "  logs                Monitor all Reddit scraper logs"
    echo "  stop                Stop all Reddit scraper processes"
    echo "  help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 simple                    # Run simple scraper in background"
    echo "  $0 configurable              # Run configurable scraper"
    echo "  $0 custom --posts 5 --comments 25  # Custom parameters"
    echo "  $0 status                    # Check what's running"
    echo "  $0 logs                      # Monitor progress"
    echo ""
    echo "Benefits:"
    echo "  ✅ Continue using Cursor while scraper runs"
    echo "  ✅ Process persists even if terminal closes"
    echo "  ✅ Monitor progress through log files"
    echo "  ✅ Multiple scrapers can run simultaneously"
}

# Function to check if virtual environment exists
check_environment() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_info "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi
    return 0
}

# Function to run simple scraper in background
run_simple_scraper() {
    print_header
    print_info "Starting Simple Reddit Scraper in Background..."

    if ! check_environment; then
        return 1
    fi

    cd "$PROJECT_DIR"

    # Generate timestamp for log file
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOGS_DIR/reddit_simple_$TIMESTAMP.log"

    print_info "Project Directory: $PROJECT_DIR"
    print_info "Log File: $LOG_FILE"
    print_info "Results Directory: $RESULTS_DIR"

    # Run in background
    source "$VENV_PATH/bin/activate" && \
    nohup python features/reddit_research/cli_reddit_scraper_simple.py > "$LOG_FILE" 2>&1 &

    # Get process ID
    PID=$!

    print_success "Simple Reddit scraper started in background!"
    print_info "Process ID: $PID"
    print_info "Log file: $LOG_FILE"

    echo ""
    print_info "Monitor progress with:"
    echo "  tail -f $LOG_FILE"
    echo ""
    print_info "Check status with:"
    echo "  ps aux | grep $PID"
    echo ""
    print_info "Stop process with:"
    echo "  kill $PID"
    echo ""
    print_success "🚀 You can now continue using Cursor while the scraper runs!"

    # Save PID for later reference
    echo "$PID" > "$LOGS_DIR/reddit_simple.pid"
}

# Function to run streaming scraper in background
run_streaming_scraper() {
    print_header
    print_info "Starting Streaming Reddit Scraper in Background..."

    if ! check_environment; then
        return 1
    fi

    cd "$PROJECT_DIR"

    # Generate timestamp for log file
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOGS_DIR/reddit_streaming_$TIMESTAMP.log"

    print_info "Project Directory: $PROJECT_DIR"
    print_info "Log File: $LOG_FILE"
    print_info "Results Directory: $RESULTS_DIR"

    # Run in background
    source "$VENV_PATH/bin/activate" && \
    nohup python features/reddit_research/cli_reddit_scraper_streaming.py > "$LOG_FILE" 2>&1 &

    # Get process ID
    PID=$!

    print_success "Streaming Reddit scraper started in background!"
    print_info "Process ID: $PID"
    print_info "Log file: $LOG_FILE"

    echo ""
    print_info "Monitor progress with:"
    echo "  tail -f $LOG_FILE"
    echo ""
    print_info "Check status with:"
    echo "  ps aux | grep $PID"
    echo ""
    print_info "Stop process with:"
    echo "  kill $PID"
    echo ""
    print_success "🚀 You can now continue using Cursor while the scraper runs!"

    # Save PID for later reference
    echo "$PID" > "$LOGS_DIR/reddit_streaming.pid"
}

# Function to run raw data collection in background
run_raw_scraper() {
    print_header
    print_info "Starting Raw Data Collection in Background..."

    if ! check_environment; then
        return 1
    fi

    cd "$PROJECT_DIR"

    # Generate timestamp for log file
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOGS_DIR/reddit_raw_$TIMESTAMP.log"

    print_info "Project Directory: $PROJECT_DIR"
    print_info "Log File: $LOG_FILE"
    print_info "Raw Data Directory: $PROJECT_DIR/features/reddit_research/raw_data"

    # Run in background
    source "$VENV_PATH/bin/activate" && \
    nohup python features/reddit_research/cli_reddit_scraper_raw.py > "$LOG_FILE" 2>&1 &

    # Get process ID
    PID=$!

    print_success "Raw data collection started in background!"
    print_info "Process ID: $PID"
    print_info "Log file: $LOG_FILE"

    echo ""
    print_info "Monitor progress with:"
    echo "  tail -f $LOG_FILE"
    echo ""
    print_success "⚡ Fast data collection running - no AI analysis delays!"

    # Save PID for later reference
    echo "$PID" > "$LOGS_DIR/reddit_raw.pid"
}

# Function to run AI analysis on collected data
run_analyzer() {
    print_header
    print_info "Starting AI Analysis Worker in Background..."

    if ! check_environment; then
        return 1
    fi

    cd "$PROJECT_DIR"

    # Generate timestamp for log file
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOGS_DIR/reddit_analyzer_$TIMESTAMP.log"

    print_info "Project Directory: $PROJECT_DIR"
    print_info "Log File: $LOG_FILE"
    print_info "Analyzing latest raw dataset..."

    # Run in background
    source "$VENV_PATH/bin/activate" && \
    nohup python features/reddit_research/cli_reddit_analyzer.py --latest > "$LOG_FILE" 2>&1 &

    # Get process ID
    PID=$!

    print_success "AI Analysis worker started in background!"
    print_info "Process ID: $PID"
    print_info "Log file: $LOG_FILE"

    echo ""
    print_info "Monitor progress with:"
    echo "  tail -f $LOG_FILE"
    echo ""
    print_success "🤖 Comprehensive AI analysis running!"

    # Save PID for later reference
    echo "$PID" > "$LOGS_DIR/reddit_analyzer.pid"
}

# Function to run full pipeline (raw collection + analysis)
run_pipeline() {
    print_header
    print_info "Starting Full Reddit Research Pipeline..."

    if ! check_environment; then
        return 1
    fi

    print_info "Pipeline Stage 1: Raw Data Collection"
    run_raw_scraper

    echo ""
    print_info "Waiting for raw data collection to complete..."
    print_info "This may take 2-5 minutes depending on data volume..."

    # Wait for raw collection to finish
    RAW_PID=$(cat "$LOGS_DIR/reddit_raw.pid" 2>/dev/null)
    if [ -n "$RAW_PID" ]; then
        while ps -p "$RAW_PID" > /dev/null 2>&1; do
            sleep 10
            print_status "Raw collection still running..." "⏳"
        done
        print_success "Raw data collection completed!"
    fi

    echo ""
    print_info "Pipeline Stage 2: AI Analysis"
    run_analyzer

    print_success "🚀 Full pipeline started! Both stages running in background."
}

# Function to run configurable scraper in background
run_configurable_scraper() {
    print_header
    print_info "Starting Configurable Reddit Scraper in Background..."

    if ! check_environment; then
        return 1
    fi

    cd "$PROJECT_DIR"

    # Generate timestamp for log file
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOGS_DIR/reddit_configurable_$TIMESTAMP.log"

    # Default parameters for background execution
    POSTS=4
    COMMENTS=20
    SUBREDDITS="artificial productivity Entrepreneur"

    print_info "Project Directory: $PROJECT_DIR"
    print_info "Log File: $LOG_FILE"
    print_info "Configuration: $POSTS posts, $COMMENTS comments, subreddits: $SUBREDDITS"

    # Run in background
    source "$VENV_PATH/bin/activate" && \
    nohup python features/reddit_research/cli_reddit_scraper_configurable.py \
        --posts $POSTS --comments $COMMENTS --subreddits $SUBREDDITS \
        > "$LOG_FILE" 2>&1 &

    # Get process ID
    PID=$!

    print_success "Configurable Reddit scraper started in background!"
    print_info "Process ID: $PID"
    print_info "Log file: $LOG_FILE"

    echo ""
    print_info "Monitor progress with:"
    echo "  tail -f $LOG_FILE"
    echo ""
    print_success "🚀 You can now continue using Cursor while the scraper runs!"

    # Save PID for later reference
    echo "$PID" > "$LOGS_DIR/reddit_configurable.pid"
}

# Function to run custom scraper with parameters
run_custom_scraper() {
    print_header
    print_info "Starting Custom Reddit Scraper in Background..."

    if ! check_environment; then
        return 1
    fi

    cd "$PROJECT_DIR"

    # Generate timestamp for log file
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$LOGS_DIR/reddit_custom_$TIMESTAMP.log"

    # Pass all arguments after 'custom' to the scraper
    shift # Remove 'custom' from arguments
    CUSTOM_ARGS="$@"

    print_info "Project Directory: $PROJECT_DIR"
    print_info "Log File: $LOG_FILE"
    print_info "Custom Arguments: $CUSTOM_ARGS"

    # Run in background
    source "$VENV_PATH/bin/activate" && \
    nohup python features/reddit_research/cli_reddit_scraper_configurable.py $CUSTOM_ARGS \
        > "$LOG_FILE" 2>&1 &

    # Get process ID
    PID=$!

    print_success "Custom Reddit scraper started in background!"
    print_info "Process ID: $PID"
    print_info "Log file: $LOG_FILE"

    echo ""
    print_info "Monitor progress with:"
    echo "  tail -f $LOG_FILE"
    echo ""
    print_success "🚀 You can now continue using Cursor while the scraper runs!"

    # Save PID for later reference
    echo "$PID" > "$LOGS_DIR/reddit_custom.pid"
}

# Function to check status of running processes
check_status() {
    print_header
    print_info "Checking Reddit Scraper Status..."
    echo ""

    # Check for running Python processes related to Reddit
    REDDIT_PROCESSES=$(ps aux | grep -E "python.*reddit" | grep -v grep)

    if [ -z "$REDDIT_PROCESSES" ]; then
        print_warning "No Reddit scraper processes currently running"
    else
        print_success "Found running Reddit scraper processes:"
        echo "$REDDIT_PROCESSES"
    fi

    echo ""

    # Check PID files
    for PID_FILE in "$LOGS_DIR"/*.pid; do
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            PROCESS_NAME=$(basename "$PID_FILE" .pid)

            if ps -p "$PID" > /dev/null 2>&1; then
                print_success "$PROCESS_NAME is running (PID: $PID)"
            else
                print_warning "$PROCESS_NAME PID file exists but process is not running"
                rm -f "$PID_FILE"
            fi
        fi
    done

    echo ""
    print_info "Recent log files:"
    ls -lt "$LOGS_DIR"/reddit_*.log 2>/dev/null | head -5
}

# Function to monitor logs
monitor_logs() {
    print_header
    print_info "Monitoring Reddit Scraper Logs..."
    echo ""

    # Find the most recent log file
    LATEST_LOG=$(ls -t "$LOGS_DIR"/reddit_*.log 2>/dev/null | head -1)

    if [ -z "$LATEST_LOG" ]; then
        print_warning "No log files found in $LOGS_DIR"
        return 1
    fi

    print_info "Monitoring: $LATEST_LOG"
    print_info "Press Ctrl+C to stop monitoring"
    echo ""

    tail -f "$LATEST_LOG"
}

# Function to stop all Reddit scraper processes
stop_scrapers() {
    print_header
    print_info "Stopping Reddit Scraper Processes..."
    echo ""

    # Stop processes using PID files
    STOPPED=0
    for PID_FILE in "$LOGS_DIR"/*.pid; do
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            PROCESS_NAME=$(basename "$PID_FILE" .pid)

            if ps -p "$PID" > /dev/null 2>&1; then
                print_info "Stopping $PROCESS_NAME (PID: $PID)..."
                kill "$PID"
                STOPPED=$((STOPPED + 1))
                rm -f "$PID_FILE"
            else
                print_warning "$PROCESS_NAME PID file exists but process is not running"
                rm -f "$PID_FILE"
            fi
        fi
    done

    # Also kill any remaining Reddit Python processes
    REDDIT_PIDS=$(ps aux | grep -E "python.*reddit" | grep -v grep | awk '{print $2}')
    for PID in $REDDIT_PIDS; do
        if [ -n "$PID" ]; then
            print_info "Stopping Reddit process (PID: $PID)..."
            kill "$PID" 2>/dev/null
            STOPPED=$((STOPPED + 1))
        fi
    done

    if [ $STOPPED -eq 0 ]; then
        print_warning "No Reddit scraper processes were running"
    else
        print_success "Stopped $STOPPED Reddit scraper process(es)"
    fi
}

# Main script logic
case "${1:-help}" in
    simple)
        run_simple_scraper
        ;;
    streaming)
        run_streaming_scraper
        ;;
    raw)
        run_raw_scraper
        ;;
    analyze)
        run_analyzer
        ;;
    pipeline)
        run_pipeline
        ;;
    configurable)
        run_configurable_scraper
        ;;
    custom)
        run_custom_scraper "$@"
        ;;
    status)
        check_status
        ;;
    logs)
        monitor_logs
        ;;
    stop)
        stop_scrapers
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
