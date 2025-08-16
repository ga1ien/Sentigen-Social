#!/usr/bin/env python3
"""
Railway startup script for FastAPI application.
Handles PORT environment variable properly and provides detailed error logging.
"""

import os
import subprocess
import sys
import traceback

# Add current directory to Python path to ensure local imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def check_imports():
    """Check if critical imports are available."""
    try:
        print("🔍 Checking critical imports...")
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
        
        import uvicorn
        print(f"✅ Uvicorn {uvicorn.__version__}")
        
        # Try to import the main app
        print("🔍 Importing main application...")
        from main import app
        print("✅ Main application imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def main():
    print("🚀 Starting Railway FastAPI deployment...")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔍 Python path: {sys.path[:3]}...")  # Show first 3 entries
    
    # List directory contents to verify files are present
    print(f"📋 Directory contents:")
    try:
        contents = os.listdir(".")
        for item in sorted(contents):
            if os.path.isdir(item):
                print(f"   📁 {item}/")
            else:
                print(f"   📄 {item}")
    except Exception as e:
        print(f"   ❌ Error listing directory: {e}")
    
    print(f"🌍 Environment variables:")
    
    # Print relevant environment variables (without sensitive data)
    env_vars = ["PORT", "LOG_LEVEL", "APP_ENV", "SUPABASE_URL"]
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        if var == "SUPABASE_URL" and value != "Not set":
            # Mask the URL for security
            value = value[:20] + "..." if len(value) > 20 else value
        print(f"   {var}: {value}")
    
    # Check imports first
    if not check_imports():
        print("❌ Import check failed. Exiting...")
        sys.exit(1)
    
    # Get port from environment variable, default to 8000
    port = os.environ.get("PORT", "8000")
    
    # Validate port is a number
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            raise ValueError("Port must be between 1 and 65535")
    except ValueError as e:
        print(f"❌ Invalid port '{port}': {e}")
        sys.exit(1)
    
    # Build uvicorn command
    cmd = [
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", str(port_int),
        "--log-level", os.environ.get("LOG_LEVEL", "info").lower(),
        "--access-log"
    ]
    
    print(f"🚀 Starting FastAPI server on port {port_int}...")
    print(f"📋 Command: {' '.join(cmd)}")
    
    # Execute uvicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        sys.exit(0)

if __name__ == "__main__":
    main()
