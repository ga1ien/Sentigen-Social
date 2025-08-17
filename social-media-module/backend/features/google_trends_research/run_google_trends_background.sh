#!/bin/bash

# Google Trends Research Background Execution Script
# Manages background execution of Google Trends research tools

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$BACKEND_DIR/venv"
LOGS_DIR="$BACKEND_DIR/logs"
PIDS_DIR="$SCRIPT_DIR/pids"

# Create necessary directories
mkdir -p "$LOGS_DIR"
mkdir -p "$PIDS_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output with timestamp
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%H:%M:%S')] $message${NC}"
}

# Function to check if pytrends is installed
check_pytrends() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        python -c "import pytrends" 2>/dev/null
        if [ $? -ne 0 ]; then
            print_status $YELLOW "⚠️ pytrends not installed. Installing..."
            pip install pytrends
            if [ $? -eq 0 ]; then
                print_status $GREEN "✅ pytrends installed successfully"
            else
                print_status $RED "❌ Failed to install pytrends"
                return 1
            fi
        else
            print_status $GREEN "✅ pytrends is available"
        fi
        deactivate
    else
        print_status $RED "❌ Virtual environment not found at $VENV_PATH"
        return 1
    fi
    return 0
}

# Function to start raw data collection
start_raw() {
    local user_id=$1
    local keywords=$2
    local timeframe=${3:-"now 7-d"}

    if [ -z "$user_id" ] || [ -z "$keywords" ]; then
        print_status $RED "❌ Usage: $0 raw <user_id> <keywords> [timeframe]"
        return 1
    fi

    check_pytrends || return 1

    local pid_file="$PIDS_DIR/google_trends_raw.pid"
    local log_file="$LOGS_DIR/google_trends_raw_$(date '+%Y%m%d_%H%M%S').log"

    if [ -f "$pid_file" ]; then
        local existing_pid=$(cat "$pid_file")
        if kill -0 "$existing_pid" 2>/dev/null; then
            print_status $YELLOW "⚠️ Google Trends raw collection already running (PID: $existing_pid)"
            return 1
        else
            rm "$pid_file"
        fi
    fi

    print_status $BLUE "🚀 Starting Google Trends raw data collection..."
    print_status $CYAN "   👤 User: $user_id"
    print_status $CYAN "   🔑 Keywords: $keywords"
    print_status $CYAN "   ⏰ Timeframe: $timeframe"
    print_status $CYAN "   📄 Log: $log_file"

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    nohup python features/google_trends_research/cli_google_trends_user_accessible.py \
        --user-id "$user_id" \
        create-config \
        --name "Background Collection $(date '+%Y%m%d_%H%M%S')" \
        --keywords "$keywords" \
        --timeframe "$timeframe" \
        --include-youtube \
        > "$log_file" 2>&1 &

    local pid=$!
    echo $pid > "$pid_file"

    deactivate

    print_status $GREEN "✅ Google Trends raw collection started (PID: $pid)"
    print_status $BLUE "📊 Monitor with: $0 logs raw"

    return 0
}

# Function to start analysis
start_analyze() {
    local user_id=$1
    local config_id=$2

    if [ -z "$user_id" ] || [ -z "$config_id" ]; then
        print_status $RED "❌ Usage: $0 analyze <user_id> <config_id>"
        return 1
    fi

    local pid_file="$PIDS_DIR/google_trends_analyze.pid"
    local log_file="$LOGS_DIR/google_trends_analyze_$(date '+%Y%m%d_%H%M%S').log"

    if [ -f "$pid_file" ]; then
        local existing_pid=$(cat "$pid_file")
        if kill -0 "$existing_pid" 2>/dev/null; then
            print_status $YELLOW "⚠️ Google Trends analysis already running (PID: $existing_pid)"
            return 1
        else
            rm "$pid_file"
        fi
    fi

    print_status $BLUE "🤖 Starting Google Trends AI analysis..."
    print_status $CYAN "   👤 User: $user_id"
    print_status $CYAN "   🆔 Config: $config_id"
    print_status $CYAN "   📄 Log: $log_file"

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    nohup python features/google_trends_research/cli_google_trends_user_accessible.py \
        --user-id "$user_id" \
        run \
        --config-id "$config_id" \
        --job-type analyze \
        > "$log_file" 2>&1 &

    local pid=$!
    echo $pid > "$pid_file"

    deactivate

    print_status $GREEN "✅ Google Trends analysis started (PID: $pid)"
    print_status $BLUE "📊 Monitor with: $0 logs analyze"

    return 0
}

# Function to start full pipeline
start_pipeline() {
    local user_id=$1
    local keywords=$2
    local timeframe=${3:-"now 7-d"}

    if [ -z "$user_id" ] || [ -z "$keywords" ]; then
        print_status $RED "❌ Usage: $0 pipeline <user_id> <keywords> [timeframe]"
        return 1
    fi

    check_pytrends || return 1

    local pid_file="$PIDS_DIR/google_trends_pipeline.pid"
    local log_file="$LOGS_DIR/google_trends_pipeline_$(date '+%Y%m%d_%H%M%S').log"

    if [ -f "$pid_file" ]; then
        local existing_pid=$(cat "$pid_file")
        if kill -0 "$existing_pid" 2>/dev/null; then
            print_status $YELLOW "⚠️ Google Trends pipeline already running (PID: $existing_pid)"
            return 1
        else
            rm "$pid_file"
        fi
    fi

    print_status $BLUE "🔄 Starting Google Trends full pipeline..."
    print_status $CYAN "   👤 User: $user_id"
    print_status $CYAN "   🔑 Keywords: $keywords"
    print_status $CYAN "   ⏰ Timeframe: $timeframe"
    print_status $CYAN "   📄 Log: $log_file"

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    # Create config and run pipeline in one go
    nohup bash -c "
        config_id=\$(python features/google_trends_research/cli_google_trends_user_accessible.py \
            --user-id '$user_id' \
            create-config \
            --name 'Pipeline $(date '+%Y%m%d_%H%M%S')' \
            --keywords '$keywords' \
            --timeframe '$timeframe' \
            --include-youtube \
            --opportunity-types 'breakout,rising,questions,video' 2>&1 | grep 'Configuration created with ID:' | cut -d':' -f2 | tr -d ' ')

        if [ -n \"\$config_id\" ]; then
            echo \"Config created: \$config_id\"
            python features/google_trends_research/cli_google_trends_user_accessible.py \
                --user-id '$user_id' \
                run \
                --config-id \"\$config_id\" \
                --job-type pipeline
        else
            echo 'Failed to create configuration'
            exit 1
        fi
    " > "$log_file" 2>&1 &

    local pid=$!
    echo $pid > "$pid_file"

    deactivate

    print_status $GREEN "✅ Google Trends pipeline started (PID: $pid)"
    print_status $BLUE "📊 Monitor with: $0 logs pipeline"

    return 0
}

# Function to show status
show_status() {
    print_status $PURPLE "📊 🔍 GOOGLE TRENDS RESEARCH STATUS"
    echo "=================================="

    local raw_pid_file="$PIDS_DIR/google_trends_raw.pid"
    local analyze_pid_file="$PIDS_DIR/google_trends_analyze.pid"
    local pipeline_pid_file="$PIDS_DIR/google_trends_pipeline.pid"

    # Check raw collection
    if [ -f "$raw_pid_file" ]; then
        local raw_pid=$(cat "$raw_pid_file")
        if kill -0 "$raw_pid" 2>/dev/null; then
            print_status $GREEN "✅ Google Trends raw: Running (PID: $raw_pid)"
        else
            print_status $RED "❌ Google Trends raw: Not running (stale PID file)"
            rm "$raw_pid_file"
        fi
    else
        print_status $RED "❌ Google Trends raw: Not running"
    fi

    # Check analysis
    if [ -f "$analyze_pid_file" ]; then
        local analyze_pid=$(cat "$analyze_pid_file")
        if kill -0 "$analyze_pid" 2>/dev/null; then
            print_status $GREEN "✅ Google Trends analyzer: Running (PID: $analyze_pid)"
        else
            print_status $RED "❌ Google Trends analyzer: Not running (stale PID file)"
            rm "$analyze_pid_file"
        fi
    else
        print_status $RED "❌ Google Trends analyzer: Not running"
    fi

    # Check pipeline
    if [ -f "$pipeline_pid_file" ]; then
        local pipeline_pid=$(cat "$pipeline_pid_file")
        if kill -0 "$pipeline_pid" 2>/dev/null; then
            print_status $GREEN "✅ Google Trends pipeline: Running (PID: $pipeline_pid)"
        else
            print_status $RED "❌ Google Trends pipeline: Not running (stale PID file)"
            rm "$pipeline_pid_file"
        fi
    else
        print_status $RED "❌ Google Trends pipeline: Not running"
    fi

    # Check if any are running
    local any_running=false
    for pid_file in "$raw_pid_file" "$analyze_pid_file" "$pipeline_pid_file"; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                any_running=true
                break
            fi
        fi
    done

    if [ "$any_running" = false ]; then
        print_status $YELLOW "⚠️ No Google Trends processes are currently running"
    fi

    echo ""
    print_status $PURPLE "📊 📁 Data directories:"
    echo "   Raw data: $SCRIPT_DIR/raw_data"
    echo "   Analyzed data: $SCRIPT_DIR/analyzed_data"
    echo "   Logs: $LOGS_DIR"
    echo "   PIDs: $PIDS_DIR"
    echo ""

    # Check pytrends availability
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        python -c "import pytrends" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_status $GREEN "📊 🔑 Google Trends API: Available (pytrends installed)"
        else
            print_status $YELLOW "📊 ⚠️ Google Trends API: pytrends not installed"
            echo "   Install with: pip install pytrends"
        fi
        deactivate
    fi

    echo ""
}

# Function to show logs
show_logs() {
    local log_type=$1

    case $log_type in
        "raw")
            local latest_log=$(ls -t "$LOGS_DIR"/google_trends_raw_*.log 2>/dev/null | head -1)
            ;;
        "analyze")
            local latest_log=$(ls -t "$LOGS_DIR"/google_trends_analyze_*.log 2>/dev/null | head -1)
            ;;
        "pipeline")
            local latest_log=$(ls -t "$LOGS_DIR"/google_trends_pipeline_*.log 2>/dev/null | head -1)
            ;;
        *)
            local latest_log=$(ls -t "$LOGS_DIR"/google_trends_*.log 2>/dev/null | head -1)
            ;;
    esac

    if [ -n "$latest_log" ] && [ -f "$latest_log" ]; then
        print_status $BLUE "📄 Showing logs from: $(basename "$latest_log")"
        echo "=================================="
        tail -f "$latest_log"
    else
        print_status $YELLOW "⚠️ No log files found for Google Trends $log_type"
        echo "Available logs:"
        ls -la "$LOGS_DIR"/google_trends_*.log 2>/dev/null || echo "   No logs found"
    fi
}

# Function to stop processes
stop_processes() {
    local process_type=$1

    case $process_type in
        "raw")
            local pid_file="$PIDS_DIR/google_trends_raw.pid"
            ;;
        "analyze")
            local pid_file="$PIDS_DIR/google_trends_analyze.pid"
            ;;
        "pipeline")
            local pid_file="$PIDS_DIR/google_trends_pipeline.pid"
            ;;
        "all")
            stop_processes "raw"
            stop_processes "analyze"
            stop_processes "pipeline"
            return 0
            ;;
        *)
            print_status $RED "❌ Unknown process type: $process_type"
            return 1
            ;;
    esac

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_status $YELLOW "🛑 Stopping Google Trends $process_type (PID: $pid)..."
            kill "$pid"
            sleep 2

            if kill -0 "$pid" 2>/dev/null; then
                print_status $YELLOW "⚠️ Process still running, force killing..."
                kill -9 "$pid"
            fi

            rm "$pid_file"
            print_status $GREEN "✅ Google Trends $process_type stopped"
        else
            print_status $YELLOW "⚠️ Google Trends $process_type not running (removing stale PID file)"
            rm "$pid_file"
        fi
    else
        print_status $YELLOW "⚠️ Google Trends $process_type not running"
    fi
}

# Function to run quick trends check
quick_trends() {
    local user_id=$1
    local keywords=$2
    local timeframe=${3:-"now 7-d"}

    if [ -z "$user_id" ] || [ -z "$keywords" ]; then
        print_status $RED "❌ Usage: $0 quick <user_id> <keywords> [timeframe]"
        return 1
    fi

    check_pytrends || return 1

    print_status $BLUE "⚡ Quick Google Trends check..."
    print_status $CYAN "   🔑 Keywords: $keywords"
    print_status $CYAN "   ⏰ Timeframe: $timeframe"

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    python features/google_trends_research/cli_google_trends_user_accessible.py \
        --user-id "$user_id" \
        quick-trends \
        --keywords "$keywords" \
        --timeframe "$timeframe"

    deactivate
}

# Main script logic
case $1 in
    "raw")
        start_raw "$2" "$3" "$4"
        ;;
    "analyze")
        start_analyze "$2" "$3"
        ;;
    "pipeline")
        start_pipeline "$2" "$3" "$4"
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "stop")
        stop_processes "$2"
        ;;
    "quick")
        quick_trends "$2" "$3" "$4"
        ;;
    *)
        echo "Google Trends Research Background Manager"
        echo "========================================"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  raw <user_id> <keywords> [timeframe]     - Start raw data collection"
        echo "  analyze <user_id> <config_id>            - Start AI analysis"
        echo "  pipeline <user_id> <keywords> [timeframe] - Start full pipeline"
        echo "  quick <user_id> <keywords> [timeframe]   - Quick trends check"
        echo "  status                                    - Show process status"
        echo "  logs [raw|analyze|pipeline]               - Show logs"
        echo "  stop [raw|analyze|pipeline|all]          - Stop processes"
        echo ""
        echo "Examples:"
        echo "  $0 pipeline user@example.com 'AI,ChatGPT,machine learning' 'now 7-d'"
        echo "  $0 quick user@example.com 'productivity,automation'"
        echo "  $0 status"
        echo "  $0 logs pipeline"
        echo "  $0 stop all"
        echo ""
        echo "Notes:"
        echo "  - Keywords should be comma-separated and quoted"
        echo "  - Timeframes: 'now 1-H', 'now 7-d', 'today 1-m', 'today 12-m', etc."
        echo "  - Requires pytrends: pip install pytrends"
        ;;
esac
