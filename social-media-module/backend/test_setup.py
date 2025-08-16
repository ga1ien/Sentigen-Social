#!/usr/bin/env python3
"""
Test script to verify the environment setup is working correctly.
"""

import sys
import os

def test_python_version():
    """Test Python version meets requirements."""
    version = sys.version_info
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 11:
        print("✅ Python version meets requirements (3.11+)")
        return True
    else:
        print("❌ Python version does not meet requirements (3.11+)")
        return False

def test_imports():
    """Test that core packages can be imported."""
    packages = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'httpx',
        'aiohttp',
        'supabase',
        'asyncpg',
        'anthropic',
        'openai',
        'dotenv'
    ]
    
    failed = []
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            failed.append(package)
    
    return len(failed) == 0

def test_environment():
    """Test environment variables."""
    env_file = '.env'
    env_example = '.env.example'
    
    if os.path.exists(env_example):
        print(f"✅ {env_example} exists")
    else:
        print(f"❌ {env_example} not found")
    
    if os.path.exists(env_file):
        print(f"✅ {env_file} exists")
    else:
        print(f"⚠️  {env_file} not found - copy from {env_example}")

def main():
    """Run all tests."""
    print("🚀 Testing Python Environment Setup")
    print("=" * 50)
    
    # Test Python version
    python_ok = test_python_version()
    print()
    
    # Test imports
    print("📦 Testing Package Imports:")
    imports_ok = test_imports()
    print()
    
    # Test environment
    print("🔧 Testing Environment:")
    test_environment()
    print()
    
    # Summary
    print("📋 Summary:")
    if python_ok and imports_ok:
        print("✅ Environment setup is working correctly!")
        print("🚀 You can now start the backend with: ./run.sh")
    else:
        print("❌ Some issues found. Please check the output above.")
    
    print("\n🌐 Expected URLs when running:")
    print("  • Frontend: http://localhost:3000")
    print("  • Backend API: http://localhost:8000")
    print("  • API Docs: http://localhost:8000/docs")
    print("  • Health Check: http://localhost:8000/health")

if __name__ == "__main__":
    main()
