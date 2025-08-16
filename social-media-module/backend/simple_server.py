#!/usr/bin/env python3
"""
Simple FastAPI server to test the environment setup.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Social Media Platform API - Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "https://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "🚀 Social Media Platform API is running!"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "message": "✅ Backend server is running successfully",
        "environment": "development"
    }

@app.get("/api/test")
async def test_endpoint():
    return {
        "message": "🎯 API endpoint working!",
        "features": [
            "✅ FastAPI server running",
            "✅ CORS configured",
            "✅ Environment setup complete",
            "🔄 Ready for full implementation"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
