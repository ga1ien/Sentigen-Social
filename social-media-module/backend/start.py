#!/usr/bin/env python3
"""
Railway startup script for the backend.
This script handles environment variable debugging and starts the FastAPI server.
"""

import os
import subprocess
import sys


def debug_environment():
    """Debug environment variables to help diagnose Railway issues."""
    print("🔍 Railway Environment Debug:")
    print(f"  Current working directory: {os.getcwd()}")
    print(f"  Python path: {sys.executable}")
    try:
        print("  Listing /app:")
        print("    ", os.listdir("/app"))
        if os.path.isdir("/app/database"):
            print("  Listing /app/database:")
            print("    ", os.listdir("/app/database"))
    except Exception as e:
        print("  Failed to list /app:", e)

    # Check all environment variables
    env_vars = {}
    for key, value in os.environ.items():
        if any(term in key.upper() for term in ["API", "KEY", "LLM", "OPENAI", "ANTHROPIC", "SUPABASE"]):
            env_vars[key] = "***SET***" if value else "NOT SET"

    print("  Environment variables:")
    for key in sorted(env_vars.keys()):
        print(f"    {key}: {env_vars[key]}")

    # Check if critical variables are missing
    critical_vars = ["ANTHROPIC_API_KEY", "LLM_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in critical_vars if not os.getenv(var)]

    if missing_vars:
        print(f"⚠️  Missing critical environment variables: {missing_vars}")
        print("🔧 Railway may not be passing environment variables to Docker container")
        return False
    else:
        print("✅ All critical environment variables are present")
        return True


def start_server():
    """Start the FastAPI server with uvicorn."""
    port = os.getenv("PORT", "8000")
    # Ensure module path is visible for imports like `database.*`
    existing_py_path = os.environ.get("PYTHONPATH", "")
    extra_paths = ["/app", "/app/api", "/app/services", "/app/core"]
    combined = ":".join([p for p in [existing_py_path, *extra_paths] if p])
    os.environ["PYTHONPATH"] = combined

    cmd = [
        "uvicorn",
        "api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        port,
        "--workers",
        "1",  # simplify import environment for Railway
        "--app-dir",
        "/app",  # ensure /app is added to sys.path
        "--access-log",
        "--log-level",
        "info",
    ]

    print(f"🚀 Starting server with command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🎯 Railway Backend Startup")

    # Debug environment
    env_ok = debug_environment()

    if not env_ok:
        print("❌ Environment check failed, but attempting to start anyway...")

    # Start the server
    start_server()
