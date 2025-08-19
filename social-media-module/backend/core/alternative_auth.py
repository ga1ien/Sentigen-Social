#!/usr/bin/env python3
"""
GPT-5's recommended authentication fix - Direct Supabase API validation
This bypasses JWT signature verification and lets Supabase validate tokens directly
"""

import os
from typing import Optional, TypedDict
import httpx
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

class VerifiedUser(TypedDict):
    id: str
    email: Optional[str]

class GPT5AuthService:
    """GPT-5's recommended authentication service using direct Supabase API"""
    
    def __init__(self) -> None:
        if not SUPABASE_ANON_KEY:
            raise RuntimeError("Missing SUPABASE_ANON_KEY")
        logger.info("🔧 GPT-5 Auth Service initialized - using direct Supabase API validation")

    async def _validate_supabase_token(self, token: str) -> Optional[VerifiedUser]:
        """Ask Supabase Auth to verify the JWT and return the user"""
        url = f"{SUPABASE_URL}/auth/v1/user"
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_ANON_KEY,
            "Accept": "application/json",
        }
        
        logger.info(f"🔍 Validating token via direct Supabase API: {url}")
        logger.info(f"Using ANON_KEY: {SUPABASE_ANON_KEY[:30]}...")
        
        timeout = httpx.Timeout(10.0, connect=10.0, read=10.0)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, headers=headers)
                
            logger.info(f"Supabase API Response: Status {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"✅ Token validation SUCCESS: User {data.get('email')} ({data.get('id')})")
                return {"id": data.get("id"), "email": data.get("email")}
            else:
                logger.error(f"❌ Token validation FAILED: {resp.status_code} - {resp.text}")
                return None
                
        except httpx.TimeoutException:
            logger.error("❌ Supabase API timeout")
            return None
        except Exception as e:
            logger.error(f"❌ Supabase API error: {e}")
            return None

    async def authenticate_user(self, token: str) -> VerifiedUser:
        """Main authentication method"""
        logger.info("🔍 Starting GPT-5 authentication method")
        
        if not token:
            logger.error("❌ No token provided")
            raise HTTPException(status_code=401, detail="No token provided")
        
        user = await self._validate_supabase_token(token)
        if not user:
            logger.error("❌ Token validation failed")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        logger.info("✅ Authentication successful using GPT-5 method")
        return user
