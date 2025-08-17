#!/bin/bash

# Stop all running scrapers gracefully
echo "🛑 STOPPING ALL SCRAPERS"
echo "========================"

# Get the backend directory path
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BACKEND_DIR"

# Function to stop a process by PID file
stop_by_pid_file() {
    local name=$1
    local pid_file="scraper_logs/${name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "🛑 Stopping $name (PID: $pid)..."
            kill "$pid"

            # Wait for graceful shutdown
            sleep 2

            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "   ⚠️  Force killing $name..."
                kill -9 "$pid"
            fi

            echo "   ✅ $name stopped"
        else
            echo "   ⚠️  $name PID $pid not running"
        fi

        rm -f "$pid_file"
    else
        echo "   ⚠️  No PID file for $name"
    fi
}

# Stop individual components
stop_by_pid_file "orchestrator"
stop_by_pid_file "linkedin"
stop_by_pid_file "substack"
stop_by_pid_file "reddit"
stop_by_pid_file "monitor"

# Kill any remaining Python scraper processes
echo ""
echo "🔍 Checking for remaining scraper processes..."
REMAINING=$(ps aux | grep python | grep -E "(scraper|orchestrator|intelligent)" | grep -v grep)

if [ -n "$REMAINING" ]; then
    echo "⚠️  Found remaining processes:"
    echo "$REMAINING"
    echo ""
    echo "🛑 Killing remaining processes..."

    # Kill by pattern
    pkill -f "python.*scraper"
    pkill -f "python.*orchestrator"
    pkill -f "python.*intelligent"

    sleep 2
    echo "   ✅ Cleanup complete"
else
    echo "   ✅ No remaining processes found"
fi

echo ""
echo "📊 FINAL STATUS:"
echo "==============="
ACTIVE=$(ps aux | grep python | grep -E "(scraper|orchestrator|intelligent)" | grep -v grep | wc -l)
echo "Active scraper processes: $ACTIVE"

if [ "$ACTIVE" -eq 0 ]; then
    echo "✅ All scrapers stopped successfully!"
else
    echo "⚠️  Some processes may still be running"
    echo "Check with: ps aux | grep python"
fi

echo ""
echo "📁 Log files preserved in scraper_logs/"
echo "🚀 Restart with: ./scripts/run_scrapers.sh"
