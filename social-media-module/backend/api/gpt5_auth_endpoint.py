#!/usr/bin/env python3
"""
Test endpoint using ONLY GPT-5's authentication method
This bypasses our current auth system entirely
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from core.alternative_auth import GPT5AuthService

router = APIRouter()
gpt5_auth_service = GPT5AuthService()

@router.get("/test-gpt5-auth")
async def test_gpt5_auth_only(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Test endpoint using ONLY GPT-5's authentication method"""
    
    try:
        # Use GPT-5's method exclusively
        verified_user = await gpt5_auth_service.authenticate_user(credentials.credentials)
        
        return {
            "success": True,
            "method": "gpt5_direct_api",
            "user_id": verified_user["id"],
            "email": verified_user["email"],
            "message": "Authentication successful using GPT-5's direct Supabase API method!"
        }
        
    except HTTPException as e:
        return {
            "success": False,
            "error": e.detail,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Unexpected error in GPT-5 authentication"
        }
