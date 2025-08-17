"""
Terminal Monitoring System for Background Scrapers
Based on proven architecture from successful scraping app
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.supabase_client import SupabaseClient


class TerminalMonitor:
    def __init__(self):
        self.supabase_client = SupabaseClient()
        self.running = False
        self.stats = {
            "total_scrapers": 0,
            "active_scrapers": 0,
            "completed_jobs": 0,
            "total_items_extracted": 0,
            "start_time": time.time(),
        }

    def clear_screen(self):
        """Clear terminal screen"""
        os.system("clear" if os.name == "posix" else "cls")

    def get_terminal_size(self):
        """Get terminal dimensions"""
        try:
            size = subprocess.run(["stty", "size"], capture_output=True, text=True)
            if size.returncode == 0:
                rows, cols = size.stdout.strip().split()
                return int(rows), int(cols)
        except:
            pass
        return 24, 80  # Default fallback

    def format_duration(self, seconds: float) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def format_number(self, num: int) -> str:
        """Format large numbers with K/M suffixes"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.1f}K"
        else:
            return str(num)

    async def get_scraper_processes(self) -> List[Dict[str, Any]]:
        """Get running scraper processes"""
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            lines = result.stdout.split("\n")

            scrapers = []
            for line in lines:
                if "python" in line and any(keyword in line for keyword in ["scraper", "intelligent", "orchestrator"]):
                    parts = line.split()
                    if len(parts) > 10:
                        scrapers.append(
                            {
                                "pid": parts[1],
                                "cpu": parts[2],
                                "memory": parts[3],
                                "command": " ".join(parts[10:])[:60] + "..."
                                if len(" ".join(parts[10:])) > 60
                                else " ".join(parts[10:]),
                            }
                        )

            return scrapers
        except Exception as e:
            return [{"error": str(e)}]

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics from database"""
        try:
            # Get recent research sessions
            result = (
                self.supabase_client.service_client.table("research_sessions")
                .select("*")
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )

            sessions = result.data if result.data else []

            # Calculate stats
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s.get("status") == "completed"])

            # Get total items from insights
            total_items = 0
            for session in sessions:
                for platform in ["linkedin_insights", "substack_insights", "reddit_insights"]:
                    insights = session.get(platform, {})
                    if isinstance(insights, dict) and "items" in insights:
                        total_items += len(insights["items"])

            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "total_items": total_items,
                "recent_sessions": sessions[:5],  # Last 5 sessions
            }

        except Exception as e:
            return {"error": str(e)}

    def render_header(self, rows: int, cols: int) -> List[str]:
        """Render header section"""
        lines = []

        # Title
        title = "🚀 SCRAPER MONITORING DASHBOARD"
        lines.append(title.center(cols))
        lines.append("=" * cols)

        # Current time and uptime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = self.format_duration(time.time() - self.stats["start_time"])

        time_line = f"⏰ {current_time} | ⏱️  Uptime: {uptime}"
        lines.append(time_line.center(cols))
        lines.append("")

        return lines

    def render_stats_section(self, db_stats: Dict, scrapers: List, cols: int) -> List[str]:
        """Render statistics section"""
        lines = []

        lines.append("📊 OVERALL STATISTICS")
        lines.append("-" * 30)

        # Database stats
        if "error" not in db_stats:
            lines.append(f"📝 Total Sessions: {db_stats.get('total_sessions', 0)}")
            lines.append(f"✅ Completed: {db_stats.get('completed_sessions', 0)}")
            lines.append(f"📄 Items Extracted: {self.format_number(db_stats.get('total_items', 0))}")
        else:
            lines.append(f"❌ Database Error: {db_stats['error']}")

        # Process stats
        lines.append(f"🔄 Active Scrapers: {len(scrapers)}")

        lines.append("")
        return lines

    def render_active_scrapers(self, scrapers: List, cols: int) -> List[str]:
        """Render active scrapers section"""
        lines = []

        lines.append("🤖 ACTIVE SCRAPERS")
        lines.append("-" * 30)

        if not scrapers:
            lines.append("   No active scrapers running")
        else:
            for i, scraper in enumerate(scrapers[:5], 1):  # Show max 5
                if "error" in scraper:
                    lines.append(f"   ❌ Error: {scraper['error']}")
                else:
                    pid = scraper.get("pid", "N/A")
                    cpu = scraper.get("cpu", "0.0")
                    memory = scraper.get("memory", "0.0")
                    command = scraper.get("command", "Unknown")

                    lines.append(f"   {i}. PID {pid} | CPU {cpu}% | MEM {memory}%")
                    lines.append(f"      {command}")

        lines.append("")
        return lines

    def render_recent_sessions(self, db_stats: Dict, cols: int) -> List[str]:
        """Render recent sessions section"""
        lines = []

        lines.append("📋 RECENT SESSIONS")
        lines.append("-" * 30)

        if "error" in db_stats or not db_stats.get("recent_sessions"):
            lines.append("   No recent sessions found")
        else:
            for session in db_stats["recent_sessions"][:3]:  # Show last 3
                session_id = session.get("id", "Unknown")[:8]
                topic = session.get("research_topic", "Unknown Topic")[:40]
                status = session.get("status", "unknown")
                created = session.get("created_at", "")

                # Format timestamp
                if created:
                    try:
                        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        time_ago = self.format_duration(time.time() - dt.timestamp())
                        time_str = f"{time_ago} ago"
                    except:
                        time_str = "Unknown time"
                else:
                    time_str = "Unknown time"

                status_emoji = "✅" if status == "completed" else "🔄" if status == "running" else "⏳"

                lines.append(f"   {status_emoji} {session_id}: {topic}")
                lines.append(f"      {time_str}")

        lines.append("")
        return lines

    def render_controls(self, cols: int) -> List[str]:
        """Render control instructions"""
        lines = []

        lines.append("🎮 CONTROLS")
        lines.append("-" * 30)
        lines.append("   q or Ctrl+C: Quit monitor")
        lines.append("   r: Refresh now")
        lines.append("   s: Show detailed stats")
        lines.append("   l: View live logs")
        lines.append("")

        return lines

    async def render_dashboard(self):
        """Render the complete dashboard"""
        self.clear_screen()

        rows, cols = self.get_terminal_size()

        # Get data
        scrapers = await self.get_scraper_processes()
        db_stats = await self.get_database_stats()

        # Build display
        display_lines = []

        # Header
        display_lines.extend(self.render_header(rows, cols))

        # Stats section
        display_lines.extend(self.render_stats_section(db_stats, scrapers, cols))

        # Active scrapers
        display_lines.extend(self.render_active_scrapers(scrapers, cols))

        # Recent sessions
        display_lines.extend(self.render_recent_sessions(db_stats, cols))

        # Controls
        display_lines.extend(self.render_controls(cols))

        # Print the dashboard
        for line in display_lines[: rows - 2]:  # Leave space for input
            print(line)

        # Status line
        print(f"🔄 Auto-refresh every 5s | Last update: {datetime.now().strftime('%H:%M:%S')}")

    async def start_monitoring(self):
        """Start the monitoring dashboard"""
        print("🚀 Starting Scraper Monitor Dashboard...")
        print("Press 'q' to quit, 'r' to refresh")

        self.running = True
        self.stats["start_time"] = time.time()

        try:
            while self.running:
                await self.render_dashboard()

                # Wait for 5 seconds or user input
                for _ in range(50):  # 5 seconds in 0.1s intervals
                    await asyncio.sleep(0.1)

                    # Check for user input (simplified)
                    # In a real implementation, you'd use proper async input handling

        except KeyboardInterrupt:
            print("\n👋 Monitor stopped by user")
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
        finally:
            self.running = False

    def stop_monitoring(self):
        """Stop the monitoring dashboard"""
        self.running = False


# Simple CLI interface
async def main():
    """Main monitoring function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            # Quick status check
            monitor = TerminalMonitor()
            scrapers = await monitor.get_scraper_processes()
            db_stats = await monitor.get_database_stats()

            print("📊 SCRAPER STATUS")
            print("=" * 30)
            print(f"Active Scrapers: {len(scrapers)}")
            if "error" not in db_stats:
                print(f"Total Sessions: {db_stats.get('total_sessions', 0)}")
                print(f"Items Extracted: {db_stats.get('total_items', 0)}")

            if scrapers:
                print("\nRunning Processes:")
                for scraper in scrapers:
                    if "error" not in scraper:
                        print(f"  PID {scraper['pid']}: {scraper['command'][:50]}...")

        elif command == "dashboard":
            # Full dashboard
            monitor = TerminalMonitor()
            await monitor.start_monitoring()

        else:
            print("Usage: python terminal_monitor.py [status|dashboard]")

    else:
        # Default to dashboard
        monitor = TerminalMonitor()
        await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
