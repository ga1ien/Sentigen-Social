#!/usr/bin/env python3
"""
Test script for Midjourney integration via CometAPI.
Run this after setting up your CometAPI key to test the integration.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

async def test_midjourney_integration():
    """Test the Midjourney worker integration."""
    print("🎨 Testing Midjourney Integration via CometAPI")
    print("=" * 50)
    
    # Check if CometAPI key is configured
    cometapi_key = os.getenv("COMETAPI_KEY")
    if not cometapi_key or cometapi_key == "your_cometapi_key_here":
        print("❌ CometAPI key not configured!")
        print("Please set COMETAPI_KEY in backend/.env")
        print("Get your key from: https://api.cometapi.com")
        return
    
    print(f"✅ CometAPI key configured: {cometapi_key[:10]}...")
    
    try:
        # Import the worker (this will test if all dependencies are available)
        from backend.workers.midjourney_worker import MidjourneyWorker
        from backend.workers.base_worker import WorkerTask
        
        print("✅ Midjourney worker imported successfully")
        
        # Initialize the worker
        worker = MidjourneyWorker()
        print("✅ Midjourney worker initialized")
        
        # Test health check
        print("\n🔍 Testing health check...")
        is_healthy = await worker.health_check()
        
        if is_healthy:
            print("✅ Midjourney worker health check passed!")
            print("🎉 Ready to generate images and videos!")
        else:
            print("⚠️  Health check failed - check your CometAPI key")
            
        print("\n📋 Available Features:")
        print("• 🖼️  Image Generation: POST /api/midjourney/image")
        print("• 🎬 Video Generation: POST /api/midjourney/video")
        print("• 📊 Task Status: GET /api/midjourney/task/{task_id}")
        print("• 🔍 Image Upscaling: POST /api/midjourney/upscale/{task_id}")
        
        print("\n🎨 Supported Styles:")
        print("• photorealistic - Realistic images")
        print("• artistic - Creative artistic style")
        print("• anime - Anime/manga style")
        print("• cinematic - Movie-like scenes")
        print("• minimalist - Clean, simple designs")
        
        print("\n📐 Supported Aspect Ratios:")
        print("• 1:1 (Square)")
        print("• 16:9 (Landscape)")
        print("• 9:16 (Portrait)")
        print("• 4:3, 3:4, and more...")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure to install dependencies: pip install -r backend/requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_midjourney_integration())
