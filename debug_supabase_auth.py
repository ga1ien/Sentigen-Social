#!/usr/bin/env python3
"""
Debug Supabase authentication methods to see what's failing
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Test token
TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IkxnN2pyUEhySEkxU2V3SzIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2x2Z3Jzd2FlbXd2bWpkYXdzdmRqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZWM1N2ZlMC02ZmZlLTQ2NjItOWExNy0yMDMxMWZlNTI1ZjUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU1NTkwOTY3LCJpYXQiOjE3NTU1ODczNjcsImVtYWlsIjoiZ0BzZW50aWdlbi5haSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJnQHNlbnRpZ2VuLmFpIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6IkdhbGVuIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiI2ZWM1N2ZlMC02ZmZlLTQ2NjItOWExNy0yMDMxMWZlNTI1ZjUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1NTU4NzM2N31dLCJzZXNzaW9uX2lkIjoiOTgwYTFiZWEtZTRjOS00NWViLTg4MjktZGM2NzU0YTZmYzc4IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.nD8QqzfwSVZe3mJpb2kv8uTCpF8fuMjmkGSFHzyitj0"

def main():
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    print(f"🔧 Environment Check:")
    print(f"   SUPABASE_URL: {url}")
    print(f"   SUPABASE_SERVICE_KEY: {'✅ Set' if service_key else '❌ Missing'} ({len(service_key) if service_key else 0} chars)")
    print(f"   SUPABASE_ANON_KEY: {'✅ Set' if anon_key else '❌ Missing'} ({len(anon_key) if anon_key else 0} chars)")
    print()

    if not url or not service_key:
        print("❌ Missing required environment variables")
        return

    # Create service client
    print("🔧 Creating Supabase service client...")
    try:
        service_client = create_client(url, service_key)
        print("✅ Service client created successfully")
    except Exception as e:
        print(f"❌ Failed to create service client: {e}")
        return

    print(f"\n🔍 Testing authentication methods with token: {TOKEN[:30]}...")

    # Test Method 1: admin.get_user_by_access_token
    print("\n1️⃣ Testing admin.get_user_by_access_token:")
    try:
        admin_response = service_client.auth.admin.get_user_by_access_token(TOKEN)
        print(f"   Response type: {type(admin_response)}")
        print(f"   Response: {admin_response}")

        if hasattr(admin_response, 'user') and admin_response.user:
            print(f"   ✅ SUCCESS - User ID: {admin_response.user.id}")
        elif isinstance(admin_response, dict) and admin_response.get('user'):
            print(f"   ✅ SUCCESS - User ID: {admin_response['user'].get('id')}")
        else:
            print(f"   ❓ Unexpected response format")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        print(f"   Exception type: {type(e)}")

    # Test Method 2: auth.get_user
    print("\n2️⃣ Testing auth.get_user:")
    try:
        auth_response = service_client.auth.get_user(TOKEN)
        print(f"   Response type: {type(auth_response)}")
        print(f"   Response: {auth_response}")

        if hasattr(auth_response, 'user') and auth_response.user:
            print(f"   ✅ SUCCESS - User ID: {auth_response.user.id}")
        elif isinstance(auth_response, dict) and auth_response.get('user'):
            print(f"   ✅ SUCCESS - User ID: {auth_response['user'].get('id')}")
        else:
            print(f"   ❓ Unexpected response format")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        print(f"   Exception type: {type(e)}")

    # Test Method 3: Temporary client approach
    print("\n3️⃣ Testing temporary client approach:")
    try:
        temp_client = create_client(url, anon_key, options={"auth": {"auto_refresh_token": False}})
        temp_client.auth.set_session({"access_token": TOKEN, "token_type": "bearer"})
        user_response = temp_client.auth.get_user()

        print(f"   Response type: {type(user_response)}")
        print(f"   Response: {user_response}")

        if hasattr(user_response, 'user') and user_response.user:
            print(f"   ✅ SUCCESS - User ID: {user_response.user.id}")
        elif isinstance(user_response, dict) and user_response.get('user'):
            print(f"   ✅ SUCCESS - User ID: {user_response['user'].get('id')}")
        else:
            print(f"   ❓ Unexpected response format")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        print(f"   Exception type: {type(e)}")

    # Test Method 4: JWT decode + admin verification (our new approach)
    print("\n4️⃣ Testing JWT decode + admin verification (new approach):")
    try:
        import jwt

        print("   Decoding JWT to extract user ID...")
        decoded = jwt.decode(TOKEN, options={"verify_signature": False})
        user_id = decoded.get("sub")

        if user_id:
            print(f"   📋 Extracted user ID: {user_id}")

            print(f"   Verifying user exists via admin.get_user_by_id...")
            admin_response = service_client.auth.admin.get_user_by_id(user_id)

            if admin_response and hasattr(admin_response, "user") and admin_response.user:
                print(f"   ✅ SUCCESS - User verified: {admin_response.user.id}")
            elif isinstance(admin_response, dict) and admin_response.get("user"):
                print(f"   ✅ SUCCESS - User verified: {admin_response['user'].get('id')}")
            else:
                print(f"   ❌ User verification failed: {admin_response}")
        else:
            print("   ❌ No user ID found in JWT")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        print(f"   Exception type: {type(e)}")

    # Test Method 5: Check available methods
    print("\n5️⃣ Available auth methods:")
    try:
        print(f"   service_client.auth methods: {[method for method in dir(service_client.auth) if not method.startswith('_')]}")
        if hasattr(service_client.auth, 'admin'):
            print(f"   service_client.auth.admin methods: {[method for method in dir(service_client.auth.admin) if not method.startswith('_')]}")
    except Exception as e:
        print(f"   ❌ Error inspecting methods: {e}")

if __name__ == "__main__":
    main()
