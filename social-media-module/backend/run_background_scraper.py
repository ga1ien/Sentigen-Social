"""
Background Scraper Runner
Runs scrapers in true background mode so you can continue using terminal
"""

import os
import subprocess
import sys
import time
from datetime import datetime


def run_scraper_background(scraper_name="enhanced_substack_scraper"):
    """Run a scraper in true background mode"""

    # Get the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    # Create logs directory
    logs_dir = os.path.join(backend_dir, "scraper_logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Scraper script path
    scraper_path = os.path.join(backend_dir, "scrapers", f"{scraper_name}.py")

    if not os.path.exists(scraper_path):
        print(f"❌ Scraper not found: {scraper_path}")
        return None

    # Log file path
    log_file = os.path.join(logs_dir, f"{scraper_name}.log")
    pid_file = os.path.join(logs_dir, f"{scraper_name}.pid")

    # Activate venv and run scraper
    venv_python = os.path.join(backend_dir, "venv", "bin", "python")

    if not os.path.exists(venv_python):
        print(f"❌ Virtual environment not found: {venv_python}")
        print("Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
        return None

    print(f"🚀 STARTING {scraper_name.upper()} IN BACKGROUND")
    print("=" * 50)
    print(f"📍 Script: {scraper_path}")
    print(f"📝 Log file: {log_file}")
    print(f"🔢 PID file: {pid_file}")
    print()

    try:
        # Start the process in background
        with open(log_file, "w") as log_f:
            process = subprocess.Popen(
                [venv_python, scraper_path],
                stdout=log_f,
                stderr=subprocess.STDOUT,
                cwd=backend_dir,
                start_new_session=True,  # This detaches it from terminal
            )

        # Save PID
        with open(pid_file, "w") as pid_f:
            pid_f.write(str(process.pid))

        print(f"✅ Scraper started successfully!")
        print(f"🔢 Process ID: {process.pid}")
        print(f"📝 Monitor logs: tail -f {log_file}")
        print(f"⏹️  Stop scraper: kill {process.pid}")
        print()
        print("🎉 You can now continue using your terminal!")
        print("   The scraper is running independently in the background.")

        return process.pid

    except Exception as e:
        print(f"❌ Failed to start scraper: {e}")
        return None


def check_scraper_status():
    """Check status of background scrapers"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(backend_dir, "scraper_logs")

    if not os.path.exists(logs_dir):
        print("📊 No scrapers have been run yet.")
        return

    print("📊 SCRAPER STATUS")
    print("=" * 30)

    # Check for PID files
    pid_files = [f for f in os.listdir(logs_dir) if f.endswith(".pid")]

    if not pid_files:
        print("   No active scrapers found.")
        return

    for pid_file in pid_files:
        scraper_name = pid_file.replace(".pid", "")
        pid_path = os.path.join(logs_dir, pid_file)
        log_path = os.path.join(logs_dir, f"{scraper_name}.log")

        try:
            with open(pid_path, "r") as f:
                pid = int(f.read().strip())

            # Check if process is still running
            try:
                os.kill(pid, 0)  # Doesn't actually kill, just checks if process exists
                status = "🟢 RUNNING"
            except OSError:
                status = "🔴 STOPPED"

            print(f"   {scraper_name}: {status} (PID: {pid})")

            # Show last few lines of log
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r") as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            print(f"      Last: {last_line[:60]}...")
                except:
                    pass

        except Exception as e:
            print(f"   {scraper_name}: ❌ ERROR ({e})")


def stop_scraper(scraper_name):
    """Stop a specific scraper"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    pid_file = os.path.join(backend_dir, "scraper_logs", f"{scraper_name}.pid")

    if not os.path.exists(pid_file):
        print(f"❌ No PID file found for {scraper_name}")
        return False

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        # Try to kill the process
        os.kill(pid, 15)  # SIGTERM for graceful shutdown
        time.sleep(2)

        # Check if it's still running
        try:
            os.kill(pid, 0)
            # Still running, force kill
            os.kill(pid, 9)  # SIGKILL
            print(f"🛑 Force stopped {scraper_name} (PID: {pid})")
        except OSError:
            print(f"✅ Gracefully stopped {scraper_name} (PID: {pid})")

        # Remove PID file
        os.remove(pid_file)
        return True

    except Exception as e:
        print(f"❌ Failed to stop {scraper_name}: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_background_scraper.py start [scraper_name]")
        print("  python run_background_scraper.py status")
        print("  python run_background_scraper.py stop [scraper_name]")
        print()
        print("Available scrapers:")
        print("  - enhanced_substack_scraper")
        print("  - linkedin_scraper")
        print("  - reddit_scraper")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        scraper_name = sys.argv[2] if len(sys.argv) > 2 else "enhanced_substack_scraper"
        run_scraper_background(scraper_name)

    elif command == "status":
        check_scraper_status()

    elif command == "stop":
        if len(sys.argv) < 3:
            print("❌ Please specify scraper name to stop")
            sys.exit(1)
        scraper_name = sys.argv[2]
        stop_scraper(scraper_name)

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
