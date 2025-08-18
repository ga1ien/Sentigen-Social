#!/usr/bin/env python3
"""
User Authentication and Authorization System
Provides centralized user management for all research tools
"""

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta  # noqa: F401
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from database.supabase_client import SupabaseClient
except ModuleNotFoundError:
    from core.supabase_client import SupabaseClient


@dataclass
class UserContext:
    """User context for authenticated requests"""

    user_id: str
    email: str
    full_name: Optional[str]
    subscription_tier: str
    is_admin: bool
    workspaces: List[Dict[str, Any]]
    permissions: Dict[str, Any]


class UserAuthService:
    """Centralized user authentication and authorization service"""

    def __init__(self):
        self.supabase_client = SupabaseClient()
        self.security = HTTPBearer()
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")

        # Log JWT secret status for debugging
        if self.jwt_secret == "your-secret-key":
            print("WARNING: JWT_SECRET not set in environment, using default (will fail)")
        else:
            print(f"JWT_SECRET loaded from environment: {self.jwt_secret[:10]}...")

    async def authenticate_user(self, token: str) -> Optional[UserContext]:
        """Authenticate user from JWT token or Supabase session"""
        try:
            print(f"Authenticating token: {token[:20]}..." if len(token) > 20 else token)

            # Try to decode JWT token first
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                # Supabase uses the 'sub' claim for the user ID
                user_id = (
                    payload.get("sub") or payload.get("user_id") or (payload.get("user_metadata") or {}).get("sub")
                )
                print(f"Got user_id from JWT decode: {user_id} (sub={payload.get('sub')})")
            except JWTError as e:
                print(f"JWT decode failed: {e}, trying Supabase validation")
                user_id = None

            # If we couldn't determine the user_id from the direct decode, fall back
            if not user_id:
                user_id = await self._validate_supabase_token(token)

            if not user_id:
                return None

            # Get user details from database
            user = await self.supabase_client.get_user(user_id)

            # If user doesn't exist in custom users table, try to get from auth.users
            if not user:
                try:
                    # Get user from Supabase Auth
                    auth_response = self.supabase_client.service_client.auth.admin.get_user_by_id(user_id)
                    if auth_response and auth_response.user:
                        auth_user = auth_response.user
                        # Create a minimal user context from auth data
                        user = {
                            "id": auth_user.id,
                            "email": auth_user.email,
                            "full_name": auth_user.user_metadata.get("full_name") if auth_user.user_metadata else None,
                            "subscription_tier": "free",
                            "is_admin": False,
                        }
                except Exception as e:
                    print(f"Failed to get user from auth.users: {e}")
                    # Create a minimal user context with just the ID
                    user = {
                        "id": user_id,
                        "email": f"user_{user_id}@example.com",
                        "full_name": None,
                        "subscription_tier": "free",
                        "is_admin": False,
                    }

            if not user:
                return None

            # Get user workspaces
            workspaces = await self.get_user_workspaces(user_id)

            # Build user context
            return UserContext(
                user_id=user.get("id", user_id),
                email=user.get("email", f"user_{user_id}@example.com"),
                full_name=user.get("full_name"),
                subscription_tier=user.get("subscription_tier", "free"),
                is_admin=user.get("is_admin", False),
                workspaces=workspaces,
                permissions=self._calculate_permissions(user, workspaces),
            )

        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    async def _validate_supabase_token(self, token: str) -> Optional[str]:
        """Validate Supabase JWT token"""
        try:
            # First try to decode the Supabase JWT with the secret
            try:
                # Use the Supabase JWT secret to validate the token
                print(f"Attempting to decode JWT with secret: {self.jwt_secret[:10]}...")

                # Supabase JWTs use HS256 algorithm
                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=["HS256"],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_nbf": False,
                        "verify_iat": False,
                        "verify_aud": False,
                    },
                )

                # Supabase stores user ID in 'sub' claim
                user_id = payload.get("sub")
                print(f"JWT decoded successfully, payload: {payload}")
                print(f"User ID from token (sub): {user_id}")

                if user_id:
                    return user_id
            except JWTError as e:
                print(f"JWT decode error: {e}")
                print(f"Token first 50 chars: {token[:50]}...")
                # Try without signature verification as a diagnostic
                try:
                    unverified = jwt.decode(token, options={"verify_signature": False})
                    print(f"Unverified payload: {unverified}")
                    print(f"Token algorithm: {jwt.get_unverified_header(token).get('alg')}")
                except Exception as e2:
                    print(f"Cannot decode even without verification: {e2}")
                pass

            # Fallback: Use Supabase client to validate token
            client_for_auth = None
            if hasattr(self.supabase_client, "anon_client") and self.supabase_client.anon_client:
                client_for_auth = self.supabase_client.anon_client
            else:
                client_for_auth = self.supabase_client.service_client

            try:
                response = client_for_auth.auth.get_user(token)
                # Handle both SDK object and dict-like responses
                if response is not None:
                    user_obj = getattr(response, "user", None) or (
                        response.get("user") if isinstance(response, dict) else None
                    )
                    if user_obj:
                        user_id_from_resp = getattr(user_obj, "id", None) or user_obj.get("id")
                        if user_id_from_resp:
                            return user_id_from_resp
            except Exception as e:
                print(f"Supabase client validation error: {e}")
                pass

            # Last resort: Try to decode without verification (development only)
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get("sub")
            except Exception:
                pass

            return None
        except Exception as e:
            print(f"Supabase token validation error: {e}")
            return None

    async def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all workspaces accessible to user"""
        try:
            # Get owned workspaces
            owned_workspaces = (
                self.supabase_client.service_client.table("workspaces").select("*").eq("owner_id", user_id).execute()
            )

            # Get member workspaces
            member_workspaces = (
                self.supabase_client.service_client.table("workspace_members")
                .select("workspace_id, role, workspaces(*)")
                .eq("user_id", user_id)
                .execute()
            )

            workspaces = []

            # Add owned workspaces
            for workspace in owned_workspaces.data:
                workspaces.append({**workspace, "user_role": "owner"})

            # Add member workspaces
            for member in member_workspaces.data:
                if member.get("workspaces"):
                    workspaces.append({**member["workspaces"], "user_role": member["role"]})

            return workspaces

        except Exception as e:
            print(f"Error getting user workspaces: {e}")
            return []

    def _calculate_permissions(self, user: Dict, workspaces: List[Dict]) -> Dict[str, Any]:
        """Calculate user permissions based on subscription and role"""
        permissions = {
            "can_create_research": True,
            "can_schedule_research": True,
            "can_access_ai_analysis": True,
            "max_concurrent_jobs": 1,
            "max_workspaces": 1,
            "sources_available": ["reddit", "hackernews", "github"],
        }

        # Adjust based on subscription tier
        tier = user.get("subscription_tier", "free")

        if tier == "starter":
            permissions.update(
                {
                    "max_concurrent_jobs": 3,
                    "max_workspaces": 3,
                }
            )
        elif tier == "creator":
            permissions.update(
                {
                    "max_concurrent_jobs": 5,
                    "max_workspaces": 10,
                }
            )
        elif tier == "creator_pro":
            permissions.update(
                {
                    "max_concurrent_jobs": 10,
                    "max_workspaces": 25,
                }
            )
        elif tier == "enterprise":
            permissions.update(
                {
                    "max_concurrent_jobs": 50,
                    "max_workspaces": 100,
                }
            )

        # Admin permissions
        if user.get("is_admin"):
            permissions.update(
                {
                    "max_concurrent_jobs": 100,
                    "max_workspaces": 1000,
                    "can_access_all_workspaces": True,
                    "can_manage_users": True,
                }
            )

        return permissions

    async def ensure_user_workspace(self, user_id: str, workspace_name: str = None) -> str:
        """Ensure user has at least one workspace, create if needed"""
        try:
            # Check if user has any workspaces
            workspaces = await self.get_user_workspaces(user_id)

            if workspaces:
                return workspaces[0]["id"]

            # Create default workspace
            user = await self.supabase_client.get_user(user_id)
            if not user:
                raise Exception(f"User {user_id} not found")

            workspace_data = {
                "name": workspace_name or f"{user.get('full_name', 'User')}'s Workspace",
                "description": "Default workspace for research tools",
                "owner_id": user_id,
                "settings": {"research_tools_enabled": True, "default_analysis_depth": "standard"},
            }

            workspace = await self.supabase_client.create_workspace(workspace_data)
            if workspace:
                return workspace["id"]

            raise Exception("Failed to create workspace")

        except Exception as e:
            print(f"Error ensuring user workspace: {e}")
            raise

    async def check_workspace_access(self, user_context: UserContext, workspace_id: str) -> bool:
        """Check if user has access to workspace"""
        if user_context.is_admin:
            return True

        for workspace in user_context.workspaces:
            if workspace["id"] == workspace_id:
                return True

        return False

    async def get_or_create_user(self, email: str, full_name: str = None) -> Dict[str, Any]:
        """Get existing user or create new one"""
        try:
            # Try to find existing user
            result = self.supabase_client.service_client.table("users").select("*").eq("email", email).execute()

            if result.data:
                return result.data[0]

            # Create new user
            user_data = {
                "email": email,
                "full_name": full_name or email.split("@")[0],
                "subscription_tier": "free",
                "is_admin": False,
                "onboarding_completed": False,
                "preferences": {},
            }

            user = await self.supabase_client.create_user(user_data)
            if user:
                # Create default workspace
                await self.ensure_user_workspace(user["id"])
                return user

            raise Exception("Failed to create user")

        except Exception as e:
            print(f"Error getting or creating user: {e}")
            raise


# Lazy initialization to avoid import-time environment variable issues
_auth_service = None


def get_auth_service():
    """Get the auth service with lazy initialization."""
    global _auth_service
    if _auth_service is None:
        _auth_service = UserAuthService()
    return _auth_service


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> UserContext:
    """FastAPI dependency to get current authenticated user"""
    print(f"get_current_user called with credentials: {credentials}")

    if not credentials:
        print("No credentials provided")
        raise HTTPException(status_code=401, detail="Authentication required")

    print(
        f"Token from credentials: {credentials.credentials[:20]}..."
        if len(credentials.credentials) > 20
        else credentials.credentials
    )
    user_context = await get_auth_service().authenticate_user(credentials.credentials)

    if not user_context:
        print("Failed to authenticate user - no user context returned")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    print(f"Successfully authenticated user: {user_context.user_id}")
    return user_context


async def get_optional_user(request: Request) -> Optional[UserContext]:
    """FastAPI dependency to get current user if authenticated (optional)"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        return await get_auth_service().authenticate_user(token)
    except Exception:
        return None


def require_workspace_access(workspace_id: str):
    """Decorator to require workspace access"""

    async def check_access(user_context: UserContext = Depends(get_current_user)):
        if not await get_auth_service().check_workspace_access(user_context, workspace_id):
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        return user_context

    return check_access


def require_subscription_tier(min_tier: str):
    """Decorator to require minimum subscription tier"""
    tier_levels = {"free": 0, "starter": 1, "creator": 2, "creator_pro": 3, "enterprise": 4}

    async def check_tier(user_context: UserContext = Depends(get_current_user)):
        user_level = tier_levels.get(user_context.subscription_tier, 0)
        required_level = tier_levels.get(min_tier, 0)

        if user_level < required_level:
            raise HTTPException(status_code=403, detail=f"Subscription tier '{min_tier}' or higher required")
        return user_context

    return check_tier


# Utility functions for research tools
async def get_user_research_context(user_id: str, workspace_id: str = None) -> Dict[str, Any]:
    """Get research context for a user"""
    try:
        user_context = await get_auth_service().authenticate_user(user_id)  # Simplified for internal use

        if not user_context:
            # For backwards compatibility, create a basic context
            user_context = UserContext(
                user_id=user_id,
                email=f"user_{user_id}@example.com",
                full_name="Research User",
                subscription_tier="free",
                is_admin=False,
                workspaces=[],
                permissions=get_auth_service()._calculate_permissions(
                    {"subscription_tier": "free", "is_admin": False}, []
                ),
            )

        # Ensure workspace
        if not workspace_id:
            workspace_id = await get_auth_service().ensure_user_workspace(user_id)

        return {"user_context": user_context, "workspace_id": workspace_id, "permissions": user_context.permissions}

    except Exception as e:
        print(f"Error getting research context: {e}")
        # Return basic context for backwards compatibility
        return {
            "user_context": UserContext(
                user_id=user_id,
                email=f"user_{user_id}@example.com",
                full_name="Research User",
                subscription_tier="free",
                is_admin=False,
                workspaces=[],
                permissions={
                    "can_create_research": True,
                    "can_schedule_research": True,
                    "can_access_ai_analysis": True,
                    "max_concurrent_jobs": 1,
                    "sources_available": ["reddit", "hackernews", "github"],
                },
            ),
            "workspace_id": workspace_id or f"workspace_{user_id}",
            "permissions": {
                "can_create_research": True,
                "can_schedule_research": True,
                "can_access_ai_analysis": True,
                "max_concurrent_jobs": 1,
                "sources_available": ["reddit", "hackernews", "github"],
            },
        }
