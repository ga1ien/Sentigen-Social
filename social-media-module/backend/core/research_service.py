#!/usr/bin/env python3
"""
Unified Research Service
Provides centralized research management for all source tools
"""

import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.user_auth import UserAuthService, UserContext
from database.supabase_client import SupabaseClient


class ResearchSource(Enum):
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"
    GITHUB = "github"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"


class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(Enum):
    RAW = "raw"
    ANALYZE = "analyze"
    PIPELINE = "pipeline"


@dataclass
class ResearchConfiguration:
    """Unified research configuration"""

    id: Optional[str]
    user_id: str
    workspace_id: str
    source_type: ResearchSource
    config_name: str
    description: str
    configuration: Dict[str, Any]
    schedule: Optional[Dict[str, Any]] = None
    auto_run_enabled: bool = False
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_run_at: Optional[str] = None


@dataclass
class ResearchJob:
    """Research job tracking"""

    id: Optional[str]
    user_id: str
    workspace_id: str
    configuration_id: Optional[str]
    source_type: ResearchSource
    job_type: JobType
    status: JobStatus
    priority: str = "normal"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    results_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ResearchService:
    """Unified research service for all source tools"""

    def __init__(self):
        self.supabase_client = SupabaseClient()
        self.auth_service = UserAuthService()

    async def create_configuration(
        self, user_context: UserContext, config: ResearchConfiguration
    ) -> Optional[ResearchConfiguration]:
        """Create a new research configuration"""
        try:
            # Check permissions
            permissions = user_context.permissions
            current_configs = await self.get_user_configurations(user_context.user_id, config.workspace_id)

            if len(current_configs) >= permissions.get("max_configurations", 5):
                raise Exception(f"Maximum configurations limit reached ({permissions.get('max_configurations', 5)})")

            # Check if source is available for user's subscription
            if config.source_type.value not in permissions.get("sources_available", []):
                raise Exception(f"Source '{config.source_type.value}' not available for your subscription tier")

            # Prepare data for database
            config_data = {
                "user_id": config.user_id,
                "workspace_id": config.workspace_id,
                "source_type": config.source_type.value,
                "config_name": config.config_name,
                "description": config.description,
                "configuration": config.configuration,
                "schedule": config.schedule or {},
                "auto_run_enabled": config.auto_run_enabled,
                "is_active": config.is_active,
            }

            result = self.supabase_client.service_client.table("research_configurations").insert(config_data).execute()

            if result.data:
                return ResearchConfiguration(**result.data[0])

            return None

        except Exception as e:
            print(f"Error creating configuration: {e}")
            raise

    async def get_configuration(self, config_id: str, user_context: UserContext) -> Optional[ResearchConfiguration]:
        """Get a specific research configuration"""
        try:
            result = (
                self.supabase_client.service_client.table("research_configurations")
                .select("*")
                .eq("id", config_id)
                .execute()
            )

            if result.data:
                config_data = result.data[0]

                # Check access
                if not await self.auth_service.check_workspace_access(user_context, config_data["workspace_id"]):
                    raise Exception("Access denied to configuration")

                return ResearchConfiguration(**config_data)

            return None

        except Exception as e:
            print(f"Error getting configuration: {e}")
            raise

    async def get_user_configurations(self, user_id: str, workspace_id: str = None) -> List[ResearchConfiguration]:
        """Get all configurations for a user"""
        try:
            query = (
                self.supabase_client.service_client.table("research_configurations").select("*").eq("user_id", user_id)
            )

            if workspace_id:
                query = query.eq("workspace_id", workspace_id)

            result = await query.execute()

            configurations = []
            for config_data in result.data:
                configurations.append(ResearchConfiguration(**config_data))

            return configurations

        except Exception as e:
            print(f"Error getting user configurations: {e}")
            return []

    async def update_configuration(
        self, config_id: str, updates: Dict[str, Any], user_context: UserContext
    ) -> Optional[ResearchConfiguration]:
        """Update a research configuration"""
        try:
            # Get existing configuration to check access
            existing = await self.get_configuration(config_id, user_context)
            if not existing:
                raise Exception("Configuration not found")

            # Update data
            updates["updated_at"] = datetime.now().isoformat()
            result = (
                await self.supabase_client.service_client.table("research_configurations")
                .update(updates)
                .eq("id", config_id)
                .execute()
            )

            if result.data:
                return ResearchConfiguration(**result.data[0])

            return None

        except Exception as e:
            print(f"Error updating configuration: {e}")
            raise

    async def delete_configuration(self, config_id: str, user_context: UserContext) -> bool:
        """Delete a research configuration"""
        try:
            # Check access
            existing = await self.get_configuration(config_id, user_context)
            if not existing:
                raise Exception("Configuration not found")

            result = (
                await self.supabase_client.service_client.table("research_configurations")
                .delete()
                .eq("id", config_id)
                .execute()
            )

            return len(result.data) > 0

        except Exception as e:
            print(f"Error deleting configuration: {e}")
            raise

    async def create_job(self, user_context: UserContext, job: ResearchJob) -> Optional[ResearchJob]:
        """Create a new research job"""
        try:
            # Check permissions
            permissions = user_context.permissions
            active_jobs = await self.get_active_jobs(user_context.user_id)

            if len(active_jobs) >= permissions.get("max_concurrent_jobs", 1):
                raise Exception(f"Maximum concurrent jobs limit reached ({permissions.get('max_concurrent_jobs', 1)})")

            # Prepare data for database
            job_data = {
                "user_id": job.user_id,
                "workspace_id": job.workspace_id,
                "configuration_id": job.configuration_id,
                "source_type": job.source_type.value,
                "job_type": job.job_type.value,
                "status": job.status.value,
                "priority": job.priority,
                "metadata": job.metadata or {},
            }

            result = await self.supabase_client.service_client.table("research_jobs").insert(job_data).execute()

            if result.data:
                return ResearchJob(**result.data[0])

            return None

        except Exception as e:
            print(f"Error creating job: {e}")
            raise

    async def get_job(self, job_id: str, user_context: UserContext) -> Optional[ResearchJob]:
        """Get a specific research job"""
        try:
            result = (
                await self.supabase_client.service_client.table("research_jobs").select("*").eq("id", job_id).execute()
            )

            if result.data:
                job_data = result.data[0]

                # Check access
                if not await self.auth_service.check_workspace_access(user_context, job_data["workspace_id"]):
                    raise Exception("Access denied to job")

                return ResearchJob(**job_data)

            return None

        except Exception as e:
            print(f"Error getting job: {e}")
            raise

    async def update_job_status(
        self, job_id: str, status: JobStatus, error_message: str = None, results_path: str = None
    ) -> bool:
        """Update job status"""
        try:
            updates = {"status": status.value, "updated_at": datetime.now().isoformat()}

            if status == JobStatus.RUNNING and not await self.get_job_field(job_id, "started_at"):
                updates["started_at"] = datetime.now().isoformat()

            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                updates["completed_at"] = datetime.now().isoformat()

            if error_message:
                updates["error_message"] = error_message

            if results_path:
                updates["results_path"] = results_path

            result = (
                await self.supabase_client.service_client.table("research_jobs")
                .update(updates)
                .eq("id", job_id)
                .execute()
            )

            return len(result.data) > 0

        except Exception as e:
            print(f"Error updating job status: {e}")
            return False

    async def get_job_field(self, job_id: str, field: str) -> Any:
        """Get a specific field from a job"""
        try:
            result = (
                await self.supabase_client.service_client.table("research_jobs")
                .select(field)
                .eq("id", job_id)
                .execute()
            )

            if result.data:
                return result.data[0].get(field)

            return None

        except Exception as e:
            print(f"Error getting job field: {e}")
            return None

    async def get_active_jobs(self, user_id: str) -> List[ResearchJob]:
        """Get all active jobs for a user"""
        try:
            result = (
                await self.supabase_client.service_client.table("research_jobs")
                .select("*")
                .eq("user_id", user_id)
                .in_("status", ["queued", "running"])
                .execute()
            )

            jobs = []
            for job_data in result.data:
                jobs.append(ResearchJob(**job_data))

            return jobs

        except Exception as e:
            print(f"Error getting active jobs: {e}")
            return []

    async def get_user_jobs(self, user_id: str, workspace_id: str = None, limit: int = 50) -> List[ResearchJob]:
        """Get jobs for a user"""
        try:
            query = (
                self.supabase_client.service_client.table("research_jobs")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
            )

            if workspace_id:
                query = query.eq("workspace_id", workspace_id)

            result = await query.execute()

            jobs = []
            for job_data in result.data:
                jobs.append(ResearchJob(**job_data))

            return jobs

        except Exception as e:
            print(f"Error getting user jobs: {e}")
            return []

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get research statistics for a user"""
        try:
            result = await self.supabase_client.service_client.rpc(
                "get_user_research_stats", {"p_user_id": user_id}
            ).execute()

            if result.data:
                return result.data

            return {}

        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {}

    async def check_user_permissions(self, user_id: str, workspace_id: str) -> Dict[str, Any]:
        """Check user permissions for research tools"""
        try:
            result = await self.supabase_client.service_client.rpc(
                "check_research_permissions", {"p_user_id": user_id, "p_workspace_id": workspace_id}
            ).execute()

            if result.data:
                return result.data

            return {}

        except Exception as e:
            print(f"Error checking permissions: {e}")
            return {}

    async def ensure_user_access(self, user_id: str, email: str = None, full_name: str = None) -> Dict[str, Any]:
        """Ensure user has access to research tools"""
        try:
            # Get or create user
            if email:
                user = await self.auth_service.get_or_create_user(email, full_name)
            else:
                user = await self.supabase_client.get_user(user_id)

            if not user:
                raise Exception("User not found and cannot be created without email")

            # Ensure user has a workspace
            workspace_id = await self.auth_service.ensure_user_workspace(user["id"])

            # Get permissions
            permissions = await self.check_user_permissions(user["id"], workspace_id)

            return {"user": user, "workspace_id": workspace_id, "permissions": permissions, "access_granted": True}

        except Exception as e:
            print(f"Error ensuring user access: {e}")
            return {"access_granted": False, "error": str(e)}


# Global research service instance
research_service = ResearchService()
