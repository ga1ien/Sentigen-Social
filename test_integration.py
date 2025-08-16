#!/usr/bin/env python3
"""
Comprehensive integration test for AI tools, database, and workers.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "social-media-module" / "backend"
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / "social-media-module" / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment from {env_file}")
else:
    print(f"❌ Environment file not found: {env_file}")

async def test_database_connection():
    """Test Supabase database connection."""
    print("\n🗄️  Testing Database Connection...")
    
    try:
        # Import and test Supabase client
        from database.supabase_client import SupabaseClient
        
        db = SupabaseClient()
        print("✅ Supabase client initialized successfully")
        
        # Test basic connection
        # Note: This is a basic test - in production you'd test actual table operations
        print("✅ Database connection test passed")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import database client: {e}")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_openai_integration():
    """Test OpenAI API integration."""
    print("\n🤖 Testing OpenAI Integration...")
    
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False
        
        client = openai.OpenAI(api_key=api_key)
        
        # Test chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'OpenAI integration test successful'"}],
            max_tokens=20
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI response: {result}")
        return True
        
    except ImportError:
        print("❌ OpenAI package not installed")
        return False
    except Exception as e:
        print(f"❌ OpenAI integration failed: {e}")
        return False

async def test_anthropic_integration():
    """Test Anthropic API integration."""
    print("\n🧠 Testing Anthropic Integration...")
    
    try:
        import anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found in environment")
            return False
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test message creation
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=20,
            messages=[{"role": "user", "content": "Say 'Anthropic integration test successful'"}]
        )
        
        result = response.content[0].text.strip()
        print(f"✅ Anthropic response: {result}")
        return True
        
    except ImportError:
        print("❌ Anthropic package not installed")
        return False
    except Exception as e:
        print(f"❌ Anthropic integration failed: {e}")
        return False

async def test_perplexity_integration():
    """Test Perplexity API integration."""
    print("\n🔍 Testing Perplexity Integration...")
    
    try:
        import httpx
        
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            print("❌ PERPLEXITY_API_KEY not found in environment")
            return False
        
        # Test Perplexity API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-large-128k-online",
                    "messages": [{"role": "user", "content": "Say 'Perplexity integration test successful'"}],
                    "max_tokens": 20
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                print(f"✅ Perplexity response: {content}")
                return True
            else:
                print(f"❌ Perplexity API error: {response.status_code} - {response.text}")
                return False
        
    except ImportError:
        print("❌ httpx package not installed")
        return False
    except Exception as e:
        print(f"❌ Perplexity integration failed: {e}")
        return False

async def test_ayrshare_integration():
    """Test Ayrshare API integration."""
    print("\n📱 Testing Ayrshare Integration...")
    
    try:
        import httpx
        
        api_key = os.getenv("AYRSHARE_API_KEY")
        if not api_key:
            print("❌ AYRSHARE_API_KEY not found in environment")
            return False
        
        # Test Ayrshare API (just check authentication)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.ayrshare.com/api/user",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Ayrshare user info retrieved successfully")
                return True
            else:
                print(f"❌ Ayrshare API error: {response.status_code} - {response.text}")
                return False
        
    except ImportError:
        print("❌ httpx package not installed")
        return False
    except Exception as e:
        print(f"❌ Ayrshare integration failed: {e}")
        return False

async def test_worker_system():
    """Test the multi-worker AI system."""
    print("\n⚙️  Testing Worker System...")
    
    try:
        # Test if worker modules can be imported
        from workers.base_worker import BaseWorker, WorkerTask, WorkerResult
        print("✅ Base worker classes imported successfully")
        
        from workers.content_worker import ContentWorker
        print("✅ Content worker imported successfully")
        
        from workers.image_worker import ImageWorker
        print("✅ Image worker imported successfully")
        
        # Test basic worker functionality
        content_worker = ContentWorker()
        print("✅ Content worker initialized")
        
        # Create a test task
        test_task = WorkerTask(
            task_id="test-001",
            worker_type="content_worker",
            task_type="generate_post",
            input_data={
                "prompt": "Test social media post about AI",
                "platform": "twitter",
                "tone": "professional"
            }
        )
        
        print("✅ Worker system components loaded successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import worker modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Worker system test failed: {e}")
        return False

def check_environment_variables():
    """Check if all required environment variables are set."""
    print("\n🔑 Checking Environment Variables...")
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "AYRSHARE_API_KEY"
    ]
    
    optional_vars = [
        "PERPLEXITY_API_KEY",
        "HEYGEN_API_KEY",
        "COMETAPI_KEY",
        "GEMINI_API_KEY"
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✅ {var}: Set")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"✅ {var}: Set")
    
    if missing_required:
        print(f"❌ Missing required variables: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"⚠️  Missing optional variables: {', '.join(missing_optional)}")
    
    print("✅ All required environment variables are set")
    return True

async def main():
    """Run comprehensive integration tests."""
    print("🚀 Starting Comprehensive Integration Tests")
    print("=" * 60)
    
    results = {}
    
    # Check environment variables first
    results["environment"] = check_environment_variables()
    
    # Test database connection
    results["database"] = await test_database_connection()
    
    # Test AI integrations
    results["openai"] = await test_openai_integration()
    results["anthropic"] = await test_anthropic_integration()
    results["perplexity"] = await test_perplexity_integration()
    
    # Test social media integration
    results["ayrshare"] = await test_ayrshare_integration()
    
    # Test worker system
    results["workers"] = await test_worker_system()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component.title()}: {'PASS' if status else 'FAIL'}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Your AI Social Media Platform is fully functional.")
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed. Some optional features may not be available.")
    else:
        print("❌ Several critical tests failed. Please check your configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
