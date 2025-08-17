#!/bin/bash

# GPT-5 Mini + Playwright Scraper Background Runner
# Based on proven architecture from successful scraping app

echo "🚀 STARTING GPT-5 MINI SCRAPERS"
echo "================================"
echo "📝 Logs will be saved to: scraper_logs/"
echo "🔍 Monitor with: tail -f scraper_logs/orchestrator.log"
echo "📊 Dashboard: python monitoring/terminal_monitor.py dashboard"
echo ""

# Create logs directory
mkdir -p scraper_logs

# Get the backend directory path
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BACKEND_DIR"

echo "📍 Working directory: $BACKEND_DIR"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "🐍 Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found at venv/bin/activate"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if required modules are installed
echo "🔍 Checking dependencies..."
python -c "import playwright, openai, supabase" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install playwright openai supabase
    playwright install chromium
fi

# Function to start a scraper in background
start_scraper() {
    local scraper_name=$1
    local script_path=$2
    local log_file="scraper_logs/${scraper_name}.log"

    echo "🚀 Starting $scraper_name..."
    nohup python "$script_path" > "$log_file" 2>&1 &
    local pid=$!

    echo "   ✅ $scraper_name started with PID: $pid"
    echo "   📝 Logs: tail -f $log_file"
    echo "$pid" > "scraper_logs/${scraper_name}.pid"

    return $pid
}

# Start orchestrator (main coordinator)
echo ""
echo "🎯 STARTING ORCHESTRATOR"
echo "------------------------"
start_scraper "orchestrator" "orchestrator/parallel_scraper_orchestrator.py"

# Wait a moment for orchestrator to initialize
sleep 3

# Start individual scrapers if requested
if [ "$1" == "all" ]; then
    echo ""
    echo "🔵 STARTING INDIVIDUAL SCRAPERS"
    echo "-------------------------------"

    start_scraper "linkedin" "scrapers/linkedin_scraper.py"
    start_scraper "substack" "scrapers/intelligent_substack_scraper.py"
    start_scraper "reddit" "scrapers/reddit_scraper.py"
fi

# Start monitoring dashboard in background
echo ""
echo "📊 STARTING MONITORING DASHBOARD"
echo "--------------------------------"
nohup python monitoring/terminal_monitor.py dashboard > scraper_logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo "   ✅ Monitor started with PID: $MONITOR_PID"
echo "$MONITOR_PID" > scraper_logs/monitor.pid

echo ""
echo "🎉 ALL SYSTEMS STARTED!"
echo "======================="
echo ""
echo "📊 MONITORING OPTIONS:"
echo "   Dashboard:     python monitoring/terminal_monitor.py dashboard"
echo "   Quick Status:  python monitoring/terminal_monitor.py status"
echo "   Live Logs:     tail -f scraper_logs/orchestrator.log"
echo "   All Logs:      tail -f scraper_logs/*.log"
echo ""
echo "🎮 MANAGEMENT COMMANDS:"
echo "   Stop All:      ./scripts/stop_scrapers.sh"
echo "   Restart:       ./scripts/restart_scrapers.sh"
echo "   Check Status:  ps aux | grep python"
echo ""
echo "📁 LOG FILES:"
ls -la scraper_logs/ 2>/dev/null || echo "   (Logs will appear as scrapers start)"
echo ""
echo "🚀 Scrapers are now running in the background!"
echo "   You can continue coding in Cursor while they work."
echo "   Use the monitoring commands above to track progress."
