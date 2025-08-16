#!/usr/bin/env python3
"""
Railway startup script for FastAPI application.
Handles PORT environment variable properly.
"""

import os
import subprocess
import sys

def main():
    # Get port from environment variable, default to 8000
    port = os.environ.get("PORT", "8000")
    
    # Validate port is a number
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            raise ValueError("Port must be between 1 and 65535")
    except ValueError as e:
        print(f"Error: Invalid port '{port}': {e}")
        sys.exit(1)
    
    # Build uvicorn command
    cmd = [
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", str(port_int),
        "--log-level", os.environ.get("LOG_LEVEL", "info").lower()
    ]
    
    print(f"Starting FastAPI server on port {port_int}...")
    print(f"Command: {' '.join(cmd)}")
    
    # Execute uvicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)

if __name__ == "__main__":
    main()
