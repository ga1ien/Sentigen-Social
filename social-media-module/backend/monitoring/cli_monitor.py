"""
Advanced CLI Monitoring Tools
Based on proven architecture from successful scraping app
Provides comprehensive command-line monitoring and management
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.supabase_client import SupabaseClient


class CLIMonitor:
    def __init__(self):
        self.supabase_client = SupabaseClient()

    async def watch_job(self, job_id: str):
        """Watch a specific job in real-time"""
        print(f"👁️  WATCHING JOB: {job_id}")
        print("=" * 50)
        print("Press Ctrl+C to stop watching")
        print()

        last_status = ""

        try:
            while True:
                # Get job details
                result = (
                    self.supabase_client.service_client.table("research_sessions")
                    .select("*")
                    .eq("id", job_id)
                    .execute()
                )

                if not result.data:
                    print(f"❌ Job {job_id} not found")
                    break

                job = result.data[0]
                current_status = json.dumps(
                    {
                        "id": job.get("id", "")[:8],
                        "status": job.get("status", "unknown"),
                        "research_topic": job.get("research_topic", "Unknown"),
                        "platforms": job.get("platforms", []),
                        "created_at": job.get("created_at", ""),
                        "updated_at": job.get("updated_at", ""),
                        "session_metadata": job.get("session_metadata", {}),
                    },
                    indent=2,
                )

                if current_status != last_status:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"🔄 [{timestamp}] Job Update:")
                    print(current_status)
                    print("-" * 50)
                    last_status = current_status

                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print("\n👋 Stopped watching job")

    async def queue_status(self):
        """Show comprehensive queue status"""
        print("📊 QUEUE STATUS")
        print("=" * 40)

        try:
            # Get session counts by status
            result = self.supabase_client.service_client.table("research_sessions").select("status").execute()

            if result.data:
                status_counts = {}
                for session in result.data:
                    status = session.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1

                print("📈 Session Counts:")
                for status, count in status_counts.items():
                    emoji = {"completed": "✅", "running": "🔄", "failed": "❌", "pending": "⏳"}.get(status, "❓")
                    print(f"   {emoji} {status.title()}: {count}")

            # Get recent running sessions
            recent_result = (
                self.supabase_client.service_client.table("research_sessions")
                .select("*")
                .eq("status", "running")
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )

            if recent_result.data:
                print("\n🔄 Currently Running:")
                for session in recent_result.data:
                    session_id = session.get("id", "Unknown")[:8]
                    topic = session.get("research_topic", "Unknown Topic")[:40]
                    created = session.get("created_at", "")

                    if created:
                        try:
                            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                            duration = datetime.now(dt.tzinfo) - dt
                            duration_str = f"{int(duration.total_seconds())}s"
                        except:
                            duration_str = "Unknown"
                    else:
                        duration_str = "Unknown"

                    print(f"   🔄 {session_id}: {topic} ({duration_str})")

            # Get recent completed sessions
            completed_result = (
                self.supabase_client.service_client.table("research_sessions")
                .select("*")
                .eq("status", "completed")
                .order("created_at", desc=True)
                .limit(3)
                .execute()
            )

            if completed_result.data:
                print("\n✅ Recently Completed:")
                for session in completed_result.data:
                    session_id = session.get("id", "Unknown")[:8]
                    topic = session.get("research_topic", "Unknown Topic")[:40]
                    platforms = session.get("platforms", [])

                    # Count extracted items
                    total_items = 0
                    insights = session.get("substack_insights", {})
                    if isinstance(insights, dict) and "articles" in insights:
                        total_items += len(insights["articles"])

                    insights = session.get("linkedin_insights", {})
                    if isinstance(insights, dict) and "posts" in insights:
                        total_items += len(insights["posts"])

                    insights = session.get("reddit_insights", {})
                    if isinstance(insights, dict) and "posts" in insights:
                        total_items += len(insights["posts"])

                    platforms_str = ", ".join(platforms) if platforms else "Unknown"
                    print(f"   ✅ {session_id}: {topic}")
                    print(f"      Platforms: {platforms_str} | Items: {total_items}")

        except Exception as e:
            print(f"❌ Error getting queue status: {e}")

    async def job_stats(self, hours: int = 24):
        """Show job statistics for the last N hours"""
        print(f"📊 JOB STATISTICS (Last {hours} hours)")
        print("=" * 50)

        try:
            # Calculate time threshold
            threshold = datetime.now() - timedelta(hours=hours)
            threshold_str = threshold.isoformat()

            # Get sessions from the last N hours
            result = (
                self.supabase_client.service_client.table("research_sessions")
                .select("*")
                .gte("created_at", threshold_str)
                .execute()
            )

            if not result.data:
                print(f"📭 No sessions found in the last {hours} hours")
                return

            sessions = result.data

            # Calculate statistics
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s.get("status") == "completed"])
            running_sessions = len([s for s in sessions if s.get("status") == "running"])
            failed_sessions = len([s for s in sessions if s.get("status") == "failed"])

            # Platform statistics
            platform_counts = {}
            total_items = 0

            for session in sessions:
                platforms = session.get("platforms", [])
                for platform in platforms:
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1

                # Count items
                for insight_key in ["substack_insights", "linkedin_insights", "reddit_insights"]:
                    insights = session.get(insight_key, {})
                    if isinstance(insights, dict):
                        if "articles" in insights:
                            total_items += len(insights["articles"])
                        elif "posts" in insights:
                            total_items += len(insights["posts"])

            # Calculate success rate
            success_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0

            # Display statistics
            print(f"📈 Overall Statistics:")
            print(f"   Total Sessions: {total_sessions}")
            print(f"   ✅ Completed: {completed_sessions}")
            print(f"   🔄 Running: {running_sessions}")
            print(f"   ❌ Failed: {failed_sessions}")
            print(f"   📊 Success Rate: {success_rate:.1f}%")
            print(f"   📄 Total Items Extracted: {total_items}")

            if platform_counts:
                print(f"\n🌐 Platform Usage:")
                for platform, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"   {platform}: {count} sessions")

            # Average session duration for completed sessions
            durations = []
            for session in sessions:
                if session.get("status") == "completed":
                    metadata = session.get("session_metadata", {})
                    if isinstance(metadata, dict) and "duration" in metadata:
                        durations.append(metadata["duration"])

            if durations:
                avg_duration = sum(durations) / len(durations)
                print(f"\n⏱️  Average Session Duration: {avg_duration:.1f}s")

        except Exception as e:
            print(f"❌ Error getting job statistics: {e}")

    def process_status(self):
        """Show running scraper processes"""
        print("🔄 PROCESS STATUS")
        print("=" * 30)

        try:
            # Get Python processes related to scrapers
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            lines = result.stdout.split("\n")

            scraper_processes = []
            for line in lines:
                if "python" in line and any(keyword in line for keyword in ["scraper", "orchestrator", "intelligent"]):
                    scraper_processes.append(line)

            if scraper_processes:
                print(f"🔄 Found {len(scraper_processes)} scraper processes:")
                for i, process in enumerate(scraper_processes, 1):
                    parts = process.split()
                    if len(parts) > 10:
                        pid = parts[1]
                        cpu = parts[2]
                        memory = parts[3]
                        command = (
                            " ".join(parts[10:])[:60] + "..."
                            if len(" ".join(parts[10:])) > 60
                            else " ".join(parts[10:])
                        )

                        print(f"   {i}. PID {pid} | CPU {cpu}% | MEM {memory}%")
                        print(f"      {command}")
            else:
                print("📭 No scraper processes currently running")

            # Check background job PIDs
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logs_dir = os.path.join(backend_dir, "scraper_logs")

            if os.path.exists(logs_dir):
                pid_files = [f for f in os.listdir(logs_dir) if f.endswith(".pid")]

                if pid_files:
                    print(f"\n📁 Background Job PIDs:")
                    for pid_file in pid_files:
                        scraper_name = pid_file.replace(".pid", "")
                        pid_path = os.path.join(logs_dir, pid_file)

                        try:
                            with open(pid_path, "r") as f:
                                pid = int(f.read().strip())

                            # Check if process is still running
                            try:
                                os.kill(pid, 0)
                                status = "🟢 RUNNING"
                            except OSError:
                                status = "🔴 STOPPED"

                            print(f"   {scraper_name}: {status} (PID: {pid})")

                        except Exception as e:
                            print(f"   {scraper_name}: ❌ ERROR ({e})")

        except Exception as e:
            print(f"❌ Error getting process status: {e}")

    async def tail_logs(self, scraper_name: str = None, lines: int = 20):
        """Show recent log entries"""
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(backend_dir, "scraper_logs")

        if not os.path.exists(logs_dir):
            print("📭 No log directory found")
            return

        if scraper_name:
            log_file = os.path.join(logs_dir, f"{scraper_name}.log")
            if os.path.exists(log_file):
                print(f"📝 LAST {lines} LINES: {scraper_name}.log")
                print("=" * 50)

                try:
                    with open(log_file, "r") as f:
                        log_lines = f.readlines()
                        for line in log_lines[-lines:]:
                            print(line.rstrip())
                except Exception as e:
                    print(f"❌ Error reading log file: {e}")
            else:
                print(f"❌ Log file not found: {scraper_name}.log")
        else:
            # Show logs from all scrapers
            log_files = [f for f in os.listdir(logs_dir) if f.endswith(".log")]

            if not log_files:
                print("📭 No log files found")
                return

            print(f"📝 RECENT LOGS FROM ALL SCRAPERS")
            print("=" * 50)

            for log_file in log_files:
                scraper_name = log_file.replace(".log", "")
                log_path = os.path.join(logs_dir, log_file)

                print(f"\n🔍 {scraper_name}:")
                print("-" * 30)

                try:
                    with open(log_path, "r") as f:
                        log_lines = f.readlines()
                        for line in log_lines[-5:]:  # Show last 5 lines per scraper
                            print(f"   {line.rstrip()}")
                except Exception as e:
                    print(f"   ❌ Error reading log: {e}")

    async def cleanup_old_sessions(self, days: int = 7):
        """Clean up old completed sessions"""
        print(f"🧹 CLEANING UP SESSIONS OLDER THAN {days} DAYS")
        print("=" * 50)

        try:
            # Calculate threshold
            threshold = datetime.now() - timedelta(days=days)
            threshold_str = threshold.isoformat()

            # Get old completed sessions
            result = (
                self.supabase_client.service_client.table("research_sessions")
                .select("id, research_topic, created_at")
                .eq("status", "completed")
                .lt("created_at", threshold_str)
                .execute()
            )

            if not result.data:
                print(f"✨ No sessions older than {days} days found")
                return

            old_sessions = result.data
            print(f"🗑️  Found {len(old_sessions)} old sessions to clean up:")

            for session in old_sessions[:10]:  # Show first 10
                session_id = session.get("id", "Unknown")[:8]
                topic = session.get("research_topic", "Unknown")[:40]
                created = session.get("created_at", "Unknown")
                print(f"   • {session_id}: {topic} ({created})")

            if len(old_sessions) > 10:
                print(f"   ... and {len(old_sessions) - 10} more")

            # Ask for confirmation
            response = input(f"\n❓ Delete these {len(old_sessions)} old sessions? (y/N): ")

            if response.lower() == "y":
                # Delete old sessions
                session_ids = [s["id"] for s in old_sessions]
                delete_result = (
                    self.supabase_client.service_client.table("research_sessions")
                    .delete()
                    .in_("id", session_ids)
                    .execute()
                )

                print(f"✅ Deleted {len(old_sessions)} old sessions")
            else:
                print("❌ Cleanup cancelled")

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Advanced CLI Monitoring Tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch a specific job")
    watch_parser.add_argument("job_id", help="Job ID to watch")

    # Status command
    subparsers.add_parser("status", help="Show queue status")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show job statistics")
    stats_parser.add_argument("--hours", type=int, default=24, help="Hours to look back (default: 24)")

    # Processes command
    subparsers.add_parser("ps", help="Show running processes")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show recent log entries")
    logs_parser.add_argument("--scraper", help="Specific scraper name")
    logs_parser.add_argument("--lines", type=int, default=20, help="Number of lines to show (default: 20)")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old sessions")
    cleanup_parser.add_argument("--days", type=int, default=7, help="Days threshold (default: 7)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    monitor = CLIMonitor()

    try:
        if args.command == "watch":
            await monitor.watch_job(args.job_id)
        elif args.command == "status":
            await monitor.queue_status()
        elif args.command == "stats":
            await monitor.job_stats(args.hours)
        elif args.command == "ps":
            monitor.process_status()
        elif args.command == "logs":
            await monitor.tail_logs(args.scraper, args.lines)
        elif args.command == "cleanup":
            await monitor.cleanup_old_sessions(args.days)

    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
