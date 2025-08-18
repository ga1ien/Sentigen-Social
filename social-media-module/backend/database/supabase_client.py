"""
Supabase client for database operations and authentication.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import asyncpg
import numpy as np
import structlog
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

logger = structlog.get_logger(__name__)


class SupabaseClient:
    """Client for Supabase database operations and authentication."""

    def __init__(self):
        """Initialize Supabase client."""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")

        if not self.url or not self.service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required")

        # Create service client (for admin operations)
        self.service_client: Client = create_client(self.url, self.service_key)

        # Create anon client (for user operations)
        if self.anon_key:
            self.anon_client: Client = create_client(self.url, self.anon_key)
        else:
            self.anon_client = None

        # PostgreSQL connection pool for vector operations
        self._pg_pool: Optional[asyncpg.Pool] = None
        self.vector_dimension = int(os.getenv("VECTOR_DIMENSION", "1536"))

        logger.info("Supabase client initialized successfully")

    @property
    def client(self) -> Client:
        """Backward-compatible alias for the service client.

        Several API modules reference `get_supabase_client().client`.
        This property ensures those references continue to work by
        returning the admin `service_client` instance.
        """
        return self.service_client

    async def _get_pg_pool(self) -> asyncpg.Pool:
        """Get or create PostgreSQL connection pool for vector operations."""
        if self._pg_pool is None:
            # Extract connection details from Supabase URL
            db_url = self.url.replace("https://", "postgresql://postgres:")
            db_url = db_url.replace(".supabase.co", ".supabase.co:5432")
            db_url = f"{db_url}?sslmode=require"

            # Use service key as password
            db_url = db_url.replace("postgres:", f"postgres:{self.service_key}@")

            self._pg_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=10, command_timeout=60)

            # Enable pgvector extension
            async with self._pg_pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        return self._pg_pool

    async def health_check(self) -> bool:
        """Check if Supabase is accessible."""
        try:
            # Test REST API connection with the social_media_posts table we added
            result = self.service_client.table("social_media_posts").select("id").limit(1).execute()

            # Test a few other core tables to ensure schema is properly deployed
            tables_to_test = ["users", "workspaces"]
            for table in tables_to_test:
                self.service_client.table(table).select("id").limit(1).execute()

            return True
        except Exception as e:
            logger.error("Supabase health check failed", error=str(e))
            return False

    # User Management
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user."""
        try:
            result = self.service_client.table("users").insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create user", error=str(e))
            return None

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            result = self.service_client.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get user", user_id=user_id, error=str(e))
            return None

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.service_client.table("users").update(updates).eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to update user", user_id=user_id, error=str(e))
            return None

    # Workspace Management
    async def create_workspace(self, workspace_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new workspace."""
        try:
            result = self.service_client.table("workspaces").insert(workspace_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create workspace", error=str(e))
            return None

    async def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get workspace by ID."""
        try:
            result = self.service_client.table("workspaces").select("*").eq("id", workspace_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get workspace", workspace_id=workspace_id, error=str(e))
            return None

    async def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all workspaces for a user."""
        try:
            result = self.service_client.table("workspaces").select("*").eq("owner_id", user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error("Failed to get user workspaces", user_id=user_id, error=str(e))
            return []

    # Social Media Posts
    async def create_post(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new social media post record."""
        try:
            result = self.service_client.table("social_media_posts").insert(post_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create post", error=str(e))
            return None

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get social media post by ID."""
        try:
            result = self.service_client.table("social_media_posts").select("*").eq("id", post_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get post", post_id=post_id, error=str(e))
            return None

    async def update_post(self, post_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update social media post."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.service_client.table("social_media_posts").update(updates).eq("id", post_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to update post", post_id=post_id, error=str(e))
            return None

    async def get_workspace_posts(self, workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get posts for a workspace."""
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

    # Worker Tasks
    async def create_worker_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new worker task record."""
        try:
            result = self.service_client.table("worker_tasks").insert(task_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create worker task", error=str(e))
            return None

    async def get_worker_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get worker task by ID."""
        try:
            result = self.service_client.table("worker_tasks").select("*").eq("id", task_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get worker task", task_id=task_id, error=str(e))
            return None

    async def update_worker_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update worker task."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.service_client.table("worker_tasks").update(updates).eq("id", task_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to update worker task", task_id=task_id, error=str(e))
            return None

    # Worker Results
    async def create_worker_result(self, result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new worker result record."""
        try:
            result = self.service_client.table("worker_results").insert(result_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create worker result", error=str(e))
            return None

    async def get_worker_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get worker result by ID."""
        try:
            result = self.service_client.table("worker_results").select("*").eq("id", result_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get worker result", result_id=result_id, error=str(e))
            return None

    async def get_task_results(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all results for a task."""
        try:
            result = self.service_client.table("worker_results").select("*").eq("task_id", task_id).execute()
            return result.data or []
        except Exception as e:
            logger.error("Failed to get task results", task_id=task_id, error=str(e))
            return []

    # Media Assets
    async def create_media_asset(self, asset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new media asset record."""
        try:
            result = self.service_client.table("media_assets").insert(asset_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to create media asset", error=str(e))
            return None

    async def get_media_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get media asset by ID."""
        try:
            result = self.service_client.table("media_assets").select("*").eq("id", asset_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Failed to get media asset", asset_id=asset_id, error=str(e))
            return None

    async def get_workspace_media(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all media assets for a workspace."""
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

    # Analytics and Reporting
    async def get_workspace_analytics(self, workspace_id: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for a workspace."""
        try:
            # Get post count
            posts_result = (
                self.service_client.table("social_media_posts")
                .select("id", count="exact")
                .eq("workspace_id", workspace_id)
                .execute()
            )

            # Get task count
            tasks_result = (
                self.service_client.table("worker_tasks")
                .select("id", count="exact")
                .eq("workspace_id", workspace_id)
                .execute()
            )

            # Get media count
            media_result = (
                self.service_client.table("media_assets")
                .select("id", count="exact")
                .eq("workspace_id", workspace_id)
                .execute()
            )

            return {
                "posts_count": posts_result.count or 0,
                "tasks_count": tasks_result.count or 0,
                "media_count": media_result.count or 0,
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("Failed to get workspace analytics", workspace_id=workspace_id, error=str(e))
            return {}

    # Authentication helpers
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        if not self.anon_client:
            return None

        try:
            result = self.anon_client.auth.sign_in_with_password({"email": email, "password": password})
            return result.user if result.user else None
        except Exception as e:
            logger.error("Failed to authenticate user", email=email, error=str(e))
            return None

    async def create_auth_user(
        self, email: str, password: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new authenticated user."""
        if not self.anon_client:
            return None

        try:
            result = self.anon_client.auth.sign_up(
                {"email": email, "password": password, "options": {"data": metadata} if metadata else None}
            )
            return result.user if result.user else None
        except Exception as e:
            logger.error("Failed to create auth user", email=email, error=str(e))
            return None

    # Vector Operations with pgvector
    async def store_embedding(
        self,
        table: str,
        record_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store content with its embedding vector."""
        try:
            pool = await self._get_pg_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {table} (id, content, embedding, metadata, created_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """,
                    record_id,
                    content,
                    embedding,
                    metadata or {},
                )

            return True
        except Exception as e:
            logger.error("Failed to store embedding", table=table, record_id=record_id, error=str(e))
            return False

    async def similarity_search(
        self,
        table: str,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform similarity search using cosine similarity."""
        try:
            pool = await self._get_pg_pool()
            async with pool.acquire() as conn:
                # Build WHERE clause for filters
                where_clause = ""
                params = [query_embedding, limit]
                param_idx = 3

                if filters:
                    conditions = []
                    for key, value in filters.items():
                        conditions.append(f"metadata->>'{key}' = ${param_idx}")
                        params.append(str(value))
                        param_idx += 1

                    if conditions:
                        where_clause = f"WHERE {' AND '.join(conditions)}"

                query = f"""
                    SELECT id, content, metadata,
                           1 - (embedding <=> $1) as similarity
                    FROM {table}
                    {where_clause}
                    ORDER BY embedding <=> $1
                    LIMIT $2
                """

                rows = await conn.fetch(query, *params)

                results = []
                for row in rows:
                    if row["similarity"] >= threshold:
                        results.append(
                            {
                                "id": row["id"],
                                "content": row["content"],
                                "metadata": row["metadata"],
                                "similarity": float(row["similarity"]),
                            }
                        )

                return results

        except Exception as e:
            logger.error("Failed to perform similarity search", table=table, error=str(e))
            return []

    async def create_vector_table(self, table_name: str) -> bool:
        """Create a table optimized for vector storage and search."""
        try:
            pool = await self._get_pg_pool()
            async with pool.acquire() as conn:
                # Create table with vector column
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        content TEXT NOT NULL,
                        embedding vector({self.vector_dimension}),
                        metadata JSONB DEFAULT '{{}}',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """
                )

                # Create vector index for fast similarity search
                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx
                    ON {table_name} USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """
                )

                # Create metadata index for filtering
                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {table_name}_metadata_idx
                    ON {table_name} USING gin (metadata);
                """
                )

                logger.info(f"Vector table {table_name} created successfully")
                return True

        except Exception as e:
            logger.error("Failed to create vector table", table=table_name, error=str(e))
            return False

    async def get_embedding_stats(self, table: str) -> Dict[str, Any]:
        """Get statistics about embeddings in a table."""
        try:
            pool = await self._get_pg_pool()
            async with pool.acquire() as conn:
                stats = await conn.fetchrow(
                    f"""
                    SELECT
                        COUNT(*) as total_embeddings,
                        AVG(array_length(embedding::float[], 1)) as avg_dimension,
                        MIN(created_at) as oldest_embedding,
                        MAX(created_at) as newest_embedding
                    FROM {table}
                    WHERE embedding IS NOT NULL
                """
                )

                return dict(stats) if stats else {}

        except Exception as e:
            logger.error("Failed to get embedding stats", table=table, error=str(e))
            return {}

    async def close(self):
        """Close database connections."""
        if self._pg_pool:
            await self._pg_pool.close()
            self._pg_pool = None
            logger.info("PostgreSQL connection pool closed")

    # Content Management Methods
    async def create_post(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new social media post."""
        try:
            result = self.service_client.table("social_media_posts").insert(post_data).execute()
            if result.data:
                logger.info("Post created successfully", post_id=result.data[0].get("id"))
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to create post", error=str(e))
            return None

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a post by ID."""
        try:
            result = self.service_client.table("social_media_posts").select("*").eq("id", post_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to get post", post_id=post_id, error=str(e))
            return None

    async def update_post(self, post_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a post."""
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            result = self.service_client.table("social_media_posts").update(update_data).eq("id", post_id).execute()
            if result.data:
                logger.info("Post updated successfully", post_id=post_id)
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to update post", post_id=post_id, error=str(e))
            return None

    async def get_workspace_posts(self, workspace_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get posts for a workspace."""
        try:
            result = (
                self.service_client.table("social_media_posts")
                .select("*")
                .eq("workspace_id", workspace_id)
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Failed to get workspace posts", workspace_id=workspace_id, error=str(e))
            return []

    async def create_media_asset(self, asset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a media asset record."""
        try:
            result = self.service_client.table("media_assets").insert(asset_data).execute()
            if result.data:
                logger.info("Media asset created successfully", asset_id=result.data[0].get("id"))
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to create media asset", error=str(e))
            return None

    async def get_workspace_media(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get media assets for a workspace."""
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

    async def create_workspace(self, workspace_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new workspace."""
        try:
            result = self.service_client.table("workspaces").insert(workspace_data).execute()
            if result.data:
                logger.info("Workspace created successfully", workspace_id=result.data[0].get("id"))
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to create workspace", error=str(e))
            return None

    async def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """Get workspaces for a user."""
        try:
            result = (
                self.service_client.table("workspaces")
                .select("*")
                .eq("owner_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Failed to get user workspaces", user_id=user_id, error=str(e))
            return []

    async def delete_record(self, table: str, record_id: str) -> bool:
        """Delete a record from a table."""
        try:
            result = self.service_client.table(table).delete().eq("id", record_id).execute()
            logger.info("Record deleted successfully", table=table, record_id=record_id)
            return True
        except Exception as e:
            logger.error("Failed to delete record", table=table, record_id=record_id, error=str(e))
            return False
