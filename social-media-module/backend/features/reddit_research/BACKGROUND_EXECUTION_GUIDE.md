# Reddit Research Background Execution Guide

## 🎯 **The Problem Solved**

**Before**: Running Reddit scrapers blocked your terminal and prevented you from using Cursor
**Now**: Run scrapers in background while continuing to use Cursor normally!

## 🚀 **Quick Start Commands**

### Option 1: Use the Background Runner Script (Recommended)

```bash
# Navigate to the script location
cd /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/features/reddit_research

# Run simple scraper in background
./run_reddit_background.sh simple

# Run configurable scraper in background
./run_reddit_background.sh configurable

# Run with custom parameters
./run_reddit_background.sh custom --posts 5 --comments 30 --subreddits artificial MachineLearning

# Check what's running
./run_reddit_background.sh status

# Monitor progress
./run_reddit_background.sh logs

# Stop all scrapers
./run_reddit_background.sh stop
```

### Option 2: Manual Background Execution

```bash
# Simple scraper in background
cd /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend && source venv/bin/activate && nohup python features/reddit_research/cli_reddit_scraper_simple.py > reddit_simple.log 2>&1 &

# Configurable scraper in background
cd /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend && source venv/bin/activate && nohup python features/reddit_research/cli_reddit_scraper_configurable.py --posts 4 --comments 20 > reddit_config.log 2>&1 &
```

## 📋 **Background Runner Features**

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `simple` | Run simple scraper with defaults | `./run_reddit_background.sh simple` |
| `configurable` | Run configurable scraper | `./run_reddit_background.sh configurable` |
| `custom` | Run with custom parameters | `./run_reddit_background.sh custom --posts 3 --comments 50` |
| `status` | Check running processes | `./run_reddit_background.sh status` |
| `logs` | Monitor latest log file | `./run_reddit_background.sh logs` |
| `stop` | Stop all Reddit scrapers | `./run_reddit_background.sh stop` |

### What Happens When You Run in Background

1. **✅ Terminal Returns Immediately** - You can continue using Cursor
2. **✅ Process Persists** - Continues even if you close terminal
3. **✅ Logging** - All output saved to timestamped log files
4. **✅ Process Tracking** - PID files for easy management
5. **✅ Multiple Scrapers** - Can run several simultaneously

## 🔍 **Monitoring Your Background Scrapers**

### Check What's Running
```bash
# Using the background runner
./run_reddit_background.sh status

# Manual check
ps aux | grep -E "python.*reddit"
```

### Monitor Progress in Real-Time
```bash
# Using the background runner (monitors latest log)
./run_reddit_background.sh logs

# Manual monitoring
tail -f /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/logs/reddit_*.log
```

### Check Results
```bash
# List result files
ls -la /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/features/reddit_research/results/

# View latest results
cat /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/features/reddit_research/results/$(ls -t *.json | head -1)
```

## 🎛️ **Configuration Options**

### Simple Scraper (Default Settings)
- **Posts per subreddit**: 6
- **Comments per post**: 15
- **Subreddits**: artificial, productivity, Entrepreneur

### Configurable Scraper Examples

```bash
# Deep dive with many comments
./run_reddit_background.sh custom --posts 3 --comments 50 --subreddits artificial

# Broad survey with many posts
./run_reddit_background.sh custom --posts 10 --comments 10 --subreddits artificial productivity SaaS Entrepreneur

# Focus on specific topic
./run_reddit_background.sh custom --posts 5 --comments 25 --query "business automation tools 2025" --subreddits productivity SaaS

# AI-focused research
./run_reddit_background.sh custom --posts 4 --comments 30 --subreddits artificial MachineLearning datascience
```

## 📁 **File Locations**

### Scripts
```
/Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/features/reddit_research/
├── run_reddit_background.sh              # Background runner script
├── cli_reddit_scraper_simple.py          # Simple scraper
├── cli_reddit_scraper_configurable.py    # Configurable scraper
└── BACKGROUND_EXECUTION_GUIDE.md         # This guide
```

### Logs and Results
```
/Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/
├── logs/
│   ├── reddit_simple_20250116_143022.log     # Timestamped log files
│   ├── reddit_configurable_20250116_143155.log
│   ├── reddit_simple.pid                     # Process ID files
│   └── reddit_configurable.pid
└── features/reddit_research/results/
    ├── simple_reddit_research_20250116_143045.json
    └── configurable_reddit_research_20250116_143201.json
```

## 🔧 **Troubleshooting**

### Common Issues and Solutions

#### "Virtual environment not found"
```bash
# Create and setup virtual environment
cd /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### "Permission denied"
```bash
# Make script executable
chmod +x /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/features/reddit_research/run_reddit_background.sh
```

#### "Process not stopping"
```bash
# Force stop all Reddit processes
pkill -f "python.*reddit"

# Or find and kill specific PID
ps aux | grep -E "python.*reddit"
kill -9 <PID>
```

#### "No log output"
```bash
# Check if process is actually running
./run_reddit_background.sh status

# Check log file permissions
ls -la /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/logs/
```

## 💡 **Pro Tips**

### 1. **Multiple Scrapers Simultaneously**
```bash
# Run different configurations at the same time
./run_reddit_background.sh custom --posts 3 --comments 50 --subreddits artificial &
./run_reddit_background.sh custom --posts 5 --comments 20 --subreddits productivity &
./run_reddit_background.sh custom --posts 4 --comments 30 --subreddits Entrepreneur &
```

### 2. **Monitor Multiple Logs**
```bash
# Monitor all Reddit logs simultaneously
tail -f /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/logs/reddit_*.log
```

### 3. **Scheduled Execution**
```bash
# Add to crontab for scheduled execution
# Run every 6 hours
0 */6 * * * /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/features/reddit_research/run_reddit_background.sh simple
```

### 4. **Resource Management**
- **CPU Usage**: Each scraper uses ~10-20% CPU during AI analysis
- **Memory**: ~200-500MB per scraper process
- **Network**: Moderate API calls (respects Reddit rate limits)
- **Disk**: Log files ~1-5MB, result files ~1-10MB

### 5. **Best Practices**
- **Start with simple scraper** to test everything works
- **Monitor first few runs** to understand timing
- **Use custom parameters** for specific research needs
- **Stop scrapers** when not needed to save resources
- **Check results regularly** to see what insights are captured

## 🎯 **Integration with Cursor Workflow**

### Typical Workflow
1. **Start scraper in background**: `./run_reddit_background.sh simple`
2. **Continue using Cursor normally** - ask questions, write code, etc.
3. **Periodically check progress**: `./run_reddit_background.sh status`
4. **Monitor when needed**: `./run_reddit_background.sh logs`
5. **Review results when complete**: Check results directory
6. **Stop when done**: `./run_reddit_background.sh stop`

### Benefits for Development
- ✅ **Uninterrupted Cursor usage** - Ask questions anytime
- ✅ **Parallel processing** - Scrape data while developing
- ✅ **Continuous insights** - Regular data collection
- ✅ **No context switching** - Stay focused on development
- ✅ **Resource efficient** - Background processes don't block UI

---

## 🚀 **Quick Reference**

```bash
# Essential commands (copy-paste ready)

# Start simple scraper
cd /Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/features/reddit_research && ./run_reddit_background.sh simple

# Check status
./run_reddit_background.sh status

# Monitor progress
./run_reddit_background.sh logs

# Stop all scrapers
./run_reddit_background.sh stop

# Custom deep research
./run_reddit_background.sh custom --posts 3 --comments 50 --subreddits artificial
```

**Now you can run Reddit scrapers in the background while continuing to use Cursor normally!** 🎉
