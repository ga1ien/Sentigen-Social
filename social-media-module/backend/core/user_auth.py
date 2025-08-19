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

        # We use Supabase service client for auth validation - no manual JWT decoding needed
        print("Using Supabase service client for JWT validation (modern approach)")

    async def authenticate_user(self, token: str) -> Optional[UserContext]:
        """Authenticate user using Supabase service client (modern approach)"""
        try:
            print(f"Authenticating token with Supabase service client: {token[:20]}..." if len(token) > 20 else token)

            # Use Supabase service client to validate the token - this handles all JWT verification
            user_id = await self._validate_supabase_token(token)

            if not user_id:
                print("Token validation failed - no user ID returned")
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
        """Validate Supabase JWT token using service client"""
        try:
            print("Validating token with Supabase service client...")

            # Method 1: Try creating a temporary client with the user token to validate it
            try:
                from supabase import create_client

                # Create a temporary client with the user's token
                temp_client = create_client(
                    self.supabase_client.url,
                    self.supabase_client.anon_key,
                    options={"auth": {"auto_refresh_token": False}},
                )

                # Set the session manually
                temp_client.auth.set_session({"access_token": token, "token_type": "bearer"})

                # Try to get the user - if this succeeds, the token is valid
                user_response = temp_client.auth.get_user()

                if user_response and hasattr(user_response, "user") and user_response.user:
                    user_id = user_response.user.id
                    print(f"✅ Token validated successfully, user ID: {user_id}")
                    return user_id
                elif isinstance(user_response, dict) and user_response.get("user"):
                    user_id = user_response["user"].get("id")
                    print(f"✅ Token validated successfully, user ID: {user_id}")
                    return user_id

            except Exception as e:
                print(f"❌ Temporary client validation failed: {e}")

            # Method 2: Use service client admin methods
            try:
                # Try admin method to get user by JWT
                admin_response = self.supabase_client.service_client.auth.admin.get_user_by_access_token(token)

                if admin_response and hasattr(admin_response, "user") and admin_response.user:
                    user_id = admin_response.user.id
                    print(f"✅ Token validated via admin method, user ID: {user_id}")
                    return user_id

            except Exception as e:
                print(f"❌ Admin validation failed: {e}")

            # Method 3: Manual JWT validation (fallback)
            try:
                # Import JWT library for manual validation
                from jose import jwt

                # Get the JWT secret from environment - use legacy secret for now
                jwt_secret = os.getenv(
                    "JWT_SECRET",
                    "AMo8kf6/8Q8tBgpl4gBjQNuTJslL6/YMaSnnUWwdTXVggoAxCxFJeiKH2r3m0O+95xYfR1p6Q4IWfSRrl64yyg==",
                )

                # Try to decode with HS256 (legacy format)
                payload = jwt.decode(token, jwt_secret, algorithms=["HS256"], options={"verify_exp": True})

                user_id = payload.get("sub")
                if user_id:
                    print(f"✅ Token validated via manual JWT decode, user ID: {user_id}")
                    return user_id

            except Exception as e:
                print(f"❌ Manual JWT validation failed: {e}")

            print("❌ All validation methods failed")
            return None

        except Exception as e:
            print(f"❌ Token validation error: {e}")
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
