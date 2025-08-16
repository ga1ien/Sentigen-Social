"""
Vercel-compatible handler for the FastAPI application.
"""

from main import app

# Export the FastAPI app for Vercel
handler = app
