"""
Supabase client rehomed under core to ensure reliable imports in containers.

Exports SupabaseClient identical to database.supabase_client.SupabaseClient
to avoid runtime ModuleNotFoundError when the /app/database package isn't present.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
import structlog
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

logger = structlog.get_logger(__name__)


class SupabaseClient:
    """Client for Supabase database operations and authentication."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")

        if not self.url or not self.service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required")

        self.service_client: Client = create_client(self.url, self.service_key)
        self.anon_client: Optional[Client] = create_client(self.url, self.anon_key) if self.anon_key else None

        self._pg_pool: Optional[asyncpg.Pool] = None
        self.vector_dimension = int(os.getenv("VECTOR_DIMENSION", "1536"))

        logger.info("Supabase client initialized successfully")

    @property
    def client(self) -> Client:
        return self.service_client

    async def _get_pg_pool(self) -> asyncpg.Pool:
        if self._pg_pool is None:
            db_url = self.url.replace("https://", "postgresql://postgres:")
            db_url = db_url.replace(".supabase.co", ".supabase.co:5432")
            db_url = f"{db_url}?sslmode=require"
            db_url = db_url.replace("postgres:", f"postgres:{self.service_key}@")

            self._pg_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=10, command_timeout=60)

            async with self._pg_pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        return self._pg_pool

    async def health_check(self) -> bool:
        try:
            self.service_client.table("social_media_posts").select("id").limit(1).execute()
            for table in ["users", "workspaces"]:
                self.service_client.table(table).select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error("Supabase health check failed", error=str(e))
            return False

    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("users").insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create user", error=str(e))
            return None

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get user", user_id=user_id, error=str(e))
            return None

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.service_client.table("users").update(updates).eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to update user", user_id=user_id, error=str(e))
            return None

    async def create_workspace(self, workspace_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("workspaces").insert(workspace_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create workspace", error=str(e))
            return None

    async def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("workspaces").select("*").eq("id", workspace_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get workspace", workspace_id=workspace_id, error=str(e))
            return None

    async def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            result = self.service_client.table("workspaces").select("*").eq("owner_id", user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error("Failed to get user workspaces", user_id=user_id, error=str(e))
            return []

    async def create_post(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("social_media_posts").insert(post_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create post", error=str(e))
            return None

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("social_media_posts").select("*").eq("id", post_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get post", post_id=post_id, error=str(e))
            return None

    async def update_post(self, post_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.service_client.table("social_media_posts").update(updates).eq("id", post_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to update post", post_id=post_id, error=str(e))
            return None

    async def get_workspace_posts(self, workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            result = (
                self.service_client.table("social_media_posts")
                .select("*")
                .eq("workspace_id", workspace_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Failed to get workspace posts", workspace_id=workspace_id, error=str(e))
            return []

    async def create_media_asset(self, asset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("media_assets").insert(asset_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create media asset", error=str(e))
            return None

    async def get_media_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("media_assets").select("*").eq("id", asset_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get media asset", asset_id=asset_id, error=str(e))
            return None

    async def get_workspace_media(self, workspace_id: str) -> List[Dict[str, Any]]:
        try:
            result = (
                self.service_client.table("media_assets")
                .select("*")
                .eq("workspace_id", workspace_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Failed to get workspace media", workspace_id=workspace_id, error=str(e))
            return []

    async def create_worker_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            result = self.service_client.table("worker_tasks").insert(task_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create worker task", error=str(e))
            return None

    async def close(self):
        if self._pg_pool:
            await self._pg_pool.close()
            self._pg_pool = None
            logger.info("PostgreSQL connection pool closed")


