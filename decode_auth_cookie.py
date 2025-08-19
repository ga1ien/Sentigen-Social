#!/usr/bin/env python3
"""
Decode the zyyn-auth-token cookie to extract the access token
"""
import base64
import json

# The cookie value from the screenshot (I can see it's base64 encoded)
# You'll need to copy the full cookie value from the DevTools
COOKIE_VALUE = "paste_your_cookie_value_here"

def decode_cookie(cookie_value):
    try:
        # Try to decode base64
        decoded_bytes = base64.b64decode(cookie_value + '==')  # Add padding just in case
        decoded_str = decoded_bytes.decode('utf-8')

        print("🔓 Decoded cookie content:")
        print(decoded_str)
        print("\n" + "="*50 + "\n")

        # Try to parse as JSON
        auth_data = json.loads(decoded_str)

        if isinstance(auth_data, dict):
            access_token = auth_data.get('access_token')
            if access_token:
                print(f"✅ ACCESS TOKEN FOUND:")
                print(f"   {access_token}")
                print(f"\n📋 Token length: {len(access_token)} characters")

                # Show other useful info
                if 'user' in auth_data:
                    user = auth_data['user']
                    print(f"👤 User email: {user.get('email')}")
                    print(f"👤 User ID: {user.get('id')}")

                return access_token
            else:
                print("❌ No access_token found in cookie")
        else:
            print("❌ Cookie is not a JSON object")

    except Exception as e:
        print(f"❌ Error decoding cookie: {e}")
        print("Make sure you copied the full cookie value")

    return None

if __name__ == "__main__":
    if COOKIE_VALUE == "paste_your_cookie_value_here":
        print("📋 Please update the COOKIE_VALUE in this script with your actual cookie value")
        print("Copy the full value of 'zyyn-auth-token' from Chrome DevTools")
    else:
        decode_cookie(COOKIE_VALUE)
