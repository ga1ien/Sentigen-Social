#!/usr/bin/env python3
"""
Unified Research API
Provides user-accessible endpoints for all research tools with proper authentication
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.research_service import (
    JobStatus,
    JobType,
    ResearchConfiguration,
    ResearchJob,
    ResearchSource,
    research_service,
)
from core.user_auth import UserContext, get_current_user, get_optional_user

# Initialize FastAPI app
app = FastAPI(
    title="Unified Research API",
    description="User-accessible research tools for Reddit, Hacker News, and GitHub",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses
class CreateConfigRequest(BaseModel):
    source_type: str = Field(..., description="Research source (reddit, hackernews, github)")
    config_name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    configuration: Dict[str, Any] = Field(..., description="Source-specific configuration")
    workspace_id: Optional[str] = Field(None, description="Workspace ID (optional)")
    auto_run_enabled: bool = Field(False, description="Enable automatic scheduling")


class UpdateConfigRequest(BaseModel):
    config_name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    auto_run_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class CreateJobRequest(BaseModel):
    configuration_id: str = Field(..., description="Configuration ID to run")
    job_type: str = Field("pipeline", description="Job type (raw, analyze, pipeline)")
    priority: str = Field("normal", description="Job priority (low, normal, high)")


class ConfigResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    source_type: str
    config_name: str
    description: Optional[str]
    configuration: Dict[str, Any]
    auto_run_enabled: bool
    is_active: bool
    created_at: str
    updated_at: str
    last_run_at: Optional[str]


class JobResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    configuration_id: Optional[str]
    source_type: str
    job_type: str
    status: str
    priority: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    results_path: Optional[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class UserStatsResponse(BaseModel):
    total_configurations: int
    active_configurations: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    sources_used: List[str]
    last_activity: Optional[str]


class PermissionsResponse(BaseModel):
    can_create_research: bool
    can_schedule_research: bool
    can_access_ai_analysis: bool
    max_concurrent_jobs: int
    max_configurations: int
    sources_available: List[str]
    subscription_tier: str
    workspace_role: str


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"}


# User info endpoint
@app.get("/user/info")
async def get_user_info(user_context: UserContext = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": user_context.user_id,
        "email": user_context.email,
        "full_name": user_context.full_name,
        "subscription_tier": user_context.subscription_tier,
        "is_admin": user_context.is_admin,
        "workspaces": user_context.workspaces,
        "permissions": user_context.permissions,
    }


# User permissions endpoint
@app.get("/user/permissions", response_model=PermissionsResponse)
async def get_user_permissions(
    workspace_id: Optional[str] = None, user_context: UserContext = Depends(get_current_user)
):
    """Get user permissions for research tools"""
    if not workspace_id and user_context.workspaces:
        workspace_id = user_context.workspaces[0]["id"]

    permissions = await research_service.check_user_permissions(user_context.user_id, workspace_id)

    return PermissionsResponse(
        can_create_research=permissions.get("can_create_research", True),
        can_schedule_research=permissions.get("can_schedule_research", True),
        can_access_ai_analysis=permissions.get("can_access_ai_analysis", True),
        max_concurrent_jobs=permissions.get("max_concurrent_jobs", 1),
        max_configurations=permissions.get("max_configurations", 5),
        sources_available=permissions.get("sources_available", []),
        subscription_tier=permissions.get("subscription_tier", "free"),
        workspace_role=permissions.get("workspace_role", "member"),
    )


# User statistics endpoint
@app.get("/user/stats", response_model=UserStatsResponse)
async def get_user_stats(user_context: UserContext = Depends(get_current_user)):
    """Get user research statistics"""
    stats = await research_service.get_user_stats(user_context.user_id)

    return UserStatsResponse(
        total_configurations=stats.get("total_configurations", 0),
        active_configurations=stats.get("active_configurations", 0),
        total_jobs=stats.get("total_jobs", 0),
        completed_jobs=stats.get("completed_jobs", 0),
        failed_jobs=stats.get("failed_jobs", 0),
        sources_used=stats.get("sources_used", []),
        last_activity=stats.get("last_activity"),
    )


# Configuration endpoints
@app.post("/configurations", response_model=ConfigResponse)
async def create_configuration(request: CreateConfigRequest, user_context: UserContext = Depends(get_current_user)):
    """Create a new research configuration"""
    try:
        # Validate source type
        if request.source_type not in ["reddit", "hackernews", "github", "linkedin", "twitter"]:
            raise HTTPException(status_code=400, detail="Invalid source type")

        # Use provided workspace or default to first available
        workspace_id = request.workspace_id
        if not workspace_id and user_context.workspaces:
            workspace_id = user_context.workspaces[0]["id"]

        if not workspace_id:
            raise HTTPException(status_code=400, detail="No workspace available")

        # Create configuration
        config = ResearchConfiguration(
            id=None,
            user_id=user_context.user_id,
            workspace_id=workspace_id,
            source_type=ResearchSource(request.source_type),
            config_name=request.config_name,
            description=request.description,
            configuration=request.configuration,
            auto_run_enabled=request.auto_run_enabled,
        )

        created_config = await research_service.create_configuration(user_context, config)

        if not created_config:
            raise HTTPException(status_code=500, detail="Failed to create configuration")

        return ConfigResponse(
            id=created_config.id,
            user_id=created_config.user_id,
            workspace_id=created_config.workspace_id,
            source_type=created_config.source_type.value,
            config_name=created_config.config_name,
            description=created_config.description,
            configuration=created_config.configuration,
            auto_run_enabled=created_config.auto_run_enabled,
            is_active=created_config.is_active,
            created_at=created_config.created_at,
            updated_at=created_config.updated_at,
            last_run_at=created_config.last_run_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/configurations", response_model=List[ConfigResponse])
async def list_configurations(
    workspace_id: Optional[str] = None,
    source_type: Optional[str] = None,
    user_context: UserContext = Depends(get_current_user),
):
    """List user's research configurations"""
    try:
        configs = await research_service.get_user_configurations(user_context.user_id, workspace_id)

        # Filter by source type if specified
        if source_type:
            configs = [c for c in configs if c.source_type.value == source_type]

        return [
            ConfigResponse(
                id=config.id,
                user_id=config.user_id,
                workspace_id=config.workspace_id,
                source_type=config.source_type.value,
                config_name=config.config_name,
                description=config.description,
                configuration=config.configuration,
                auto_run_enabled=config.auto_run_enabled,
                is_active=config.is_active,
                created_at=config.created_at,
                updated_at=config.updated_at,
                last_run_at=config.last_run_at,
            )
            for config in configs
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/configurations/{config_id}", response_model=ConfigResponse)
async def get_configuration(config_id: str, user_context: UserContext = Depends(get_current_user)):
    """Get a specific research configuration"""
    try:
        config = await research_service.get_configuration(config_id, user_context)

        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return ConfigResponse(
            id=config.id,
            user_id=config.user_id,
            workspace_id=config.workspace_id,
            source_type=config.source_type.value,
            config_name=config.config_name,
            description=config.description,
            configuration=config.configuration,
            auto_run_enabled=config.auto_run_enabled,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            last_run_at=config.last_run_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/configurations/{config_id}", response_model=ConfigResponse)
async def update_configuration(
    config_id: str, request: UpdateConfigRequest, user_context: UserContext = Depends(get_current_user)
):
    """Update a research configuration"""
    try:
        # Prepare updates
        updates = {}
        if request.config_name is not None:
            updates["config_name"] = request.config_name
        if request.description is not None:
            updates["description"] = request.description
        if request.configuration is not None:
            updates["configuration"] = request.configuration
        if request.auto_run_enabled is not None:
            updates["auto_run_enabled"] = request.auto_run_enabled
        if request.is_active is not None:
            updates["is_active"] = request.is_active

        updated_config = await research_service.update_configuration(config_id, updates, user_context)

        if not updated_config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return ConfigResponse(
            id=updated_config.id,
            user_id=updated_config.user_id,
            workspace_id=updated_config.workspace_id,
            source_type=updated_config.source_type.value,
            config_name=updated_config.config_name,
            description=updated_config.description,
            configuration=updated_config.configuration,
            auto_run_enabled=updated_config.auto_run_enabled,
            is_active=updated_config.is_active,
            created_at=updated_config.created_at,
            updated_at=updated_config.updated_at,
            last_run_at=updated_config.last_run_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/configurations/{config_id}")
async def delete_configuration(config_id: str, user_context: UserContext = Depends(get_current_user)):
    """Delete a research configuration"""
    try:
        success = await research_service.delete_configuration(config_id, user_context)

        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return {"message": "Configuration deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Job endpoints
@app.post("/jobs", response_model=JobResponse)
async def create_job(
    request: CreateJobRequest, background_tasks: BackgroundTasks, user_context: UserContext = Depends(get_current_user)
):
    """Create and start a research job"""
    try:
        # Get configuration to determine source type and workspace
        config = await research_service.get_configuration(request.configuration_id, user_context)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Create job
        job = ResearchJob(
            id=None,
            user_id=user_context.user_id,
            workspace_id=config.workspace_id,
            configuration_id=request.configuration_id,
            source_type=config.source_type,
            job_type=JobType(request.job_type),
            status=JobStatus.QUEUED,
            priority=request.priority,
            metadata={"started_by": "api", "api_version": "1.0"},
        )

        created_job = await research_service.create_job(user_context, job)

        if not created_job:
            raise HTTPException(status_code=500, detail="Failed to create job")

        # Add background task to execute the job
        background_tasks.add_task(execute_research_job, created_job.id, config)

        return JobResponse(
            id=created_job.id,
            user_id=created_job.user_id,
            workspace_id=created_job.workspace_id,
            configuration_id=created_job.configuration_id,
            source_type=created_job.source_type.value,
            job_type=created_job.job_type.value,
            status=created_job.status.value,
            priority=created_job.priority,
            started_at=created_job.started_at,
            completed_at=created_job.completed_at,
            error_message=created_job.error_message,
            results_path=created_job.results_path,
            metadata=created_job.metadata or {},
            created_at=created_job.created_at,
            updated_at=created_job.updated_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    workspace_id: Optional[str] = None,
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    user_context: UserContext = Depends(get_current_user),
):
    """List user's research jobs"""
    try:
        jobs = await research_service.get_user_jobs(user_context.user_id, workspace_id, limit)

        # Filter by source type if specified
        if source_type:
            jobs = [j for j in jobs if j.source_type.value == source_type]

        # Filter by status if specified
        if status:
            jobs = [j for j in jobs if j.status.value == status]

        return [
            JobResponse(
                id=job.id,
                user_id=job.user_id,
                workspace_id=job.workspace_id,
                configuration_id=job.configuration_id,
                source_type=job.source_type.value,
                job_type=job.job_type.value,
                status=job.status.value,
                priority=job.priority,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error_message=job.error_message,
                results_path=job.results_path,
                metadata=job.metadata or {},
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
            for job in jobs
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, user_context: UserContext = Depends(get_current_user)):
    """Get a specific research job"""
    try:
        job = await research_service.get_job(job_id, user_context)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobResponse(
            id=job.id,
            user_id=job.user_id,
            workspace_id=job.workspace_id,
            configuration_id=job.configuration_id,
            source_type=job.source_type.value,
            job_type=job.job_type.value,
            status=job.status.value,
            priority=job.priority,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            results_path=job.results_path,
            metadata=job.metadata or {},
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Background task to execute research jobs
async def execute_research_job(job_id: str, config: ResearchConfiguration):
    """Execute a research job in the background"""
    try:
        # Update job status to running
        await research_service.update_job_status(job_id, JobStatus.RUNNING)

        # Execute based on source type
        if config.source_type == ResearchSource.REDDIT:
            # Import and execute Reddit research
            from features.reddit_research.cli_reddit_user_accessible import UserAccessibleRedditCLI

            cli = UserAccessibleRedditCLI()
            await cli.initialize(config.user_id)
            await cli.run_research_job(config.id, "pipeline")

        elif config.source_type == ResearchSource.HACKERNEWS:
            # Import and execute Hacker News research
            from features.hackernews_research.cli_hackernews_user_accessible import UserAccessibleHackerNewsCLI

            cli = UserAccessibleHackerNewsCLI()
            await cli.initialize(config.user_id)
            await cli.run_research_job(config.id, "pipeline")

        elif config.source_type == ResearchSource.GITHUB:
            # Import and execute GitHub research
            from features.github_research.cli_github_user_accessible import UserAccessibleGitHubCLI

            cli = UserAccessibleGitHubCLI()
            await cli.initialize(config.user_id)
            await cli.run_research_job(config.id, "pipeline")

        # Update job status to completed
        await research_service.update_job_status(job_id, JobStatus.COMPLETED)

    except Exception as e:
        # Update job status to failed
        await research_service.update_job_status(job_id, JobStatus.FAILED, error_message=str(e))


if __name__ == "__main__":
    uvicorn.run("unified_research_api:app", host="0.0.0.0", port=8000, reload=True)
