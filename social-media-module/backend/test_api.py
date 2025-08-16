#!/usr/bin/env python3
"""
Simple test script for the AI Social Media Platform API.
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_api():
    """Test the API endpoints."""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing AI Social Media Platform API")
        print("=" * 50)
        
        # Test health check
        print("\n1. Testing health check...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data['status']}")
                print(f"   Services: {health_data.get('services', {})}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test root endpoint
        print("\n2. Testing root endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                root_data = response.json()
                print(f"✅ Root endpoint: {root_data['name']} v{root_data['version']}")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
        
        # Test content generation (without auth for now)
        print("\n3. Testing content generation...")
        try:
            content_request = {
                "prompt": "Create an engaging LinkedIn post about AI and productivity",
                "content_type": "text",
                "platforms": ["linkedin"],
                "tone": "professional",
                "length": "medium",
                "include_hashtags": True,
                "include_emojis": False,
                "ai_provider": "anthropic"
            }
            
            # This will fail without proper auth, but we can test the endpoint structure
            response = await client.post(
                f"{BASE_URL}/api/content/generate",
                json=content_request,
                headers={"Authorization": "Bearer test-token"}
            )
            
            if response.status_code == 401:
                print("✅ Content generation endpoint exists (auth required)")
            elif response.status_code == 200:
                print("✅ Content generation successful")
                content_data = response.json()
                print(f"   Generated {len(content_data.get('variations', []))} variations")
            else:
                print(f"⚠️  Content generation response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Content generation error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 API test completed!")
        print("\nNext steps:")
        print("1. Set up Supabase database with proper schema")
        print("2. Configure authentication")
        print("3. Add API keys for AI providers")
        print("4. Test with real data")

if __name__ == "__main__":
    asyncio.run(test_api())
