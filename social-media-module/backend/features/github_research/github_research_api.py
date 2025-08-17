#!/usr/bin/env python3
"""
GitHub Research REST API
Provides endpoints for managing GitHub research configurations and jobs
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from features.github_research.github_research_config import (
    AnalysisDepth,
    GitHubConfig,
    GitHubContentType,
    GitHubResearchConfig,
    GitHubResearchConfigManager,
    GitHubTimeRange,
    ResearchFrequency,
    ResearchSchedule,
)

app = FastAPI(title="GitHub Research API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize config manager
config_manager = GitHubResearchConfigManager()


# Pydantic models for API requests/responses
class GitHubConfigRequest(BaseModel):
    content_types: List[str] = Field(..., example=["trending_repos", "viral_repos"])
    search_topics: List[str] = Field(..., example=["AI", "machine learning", "web development"])
    languages: List[str] = Field(default_factory=list, example=["Python", "JavaScript", "TypeScript"])
    max_repos_per_search: int = Field(20, ge=1, le=100)
    min_stars: int = Field(100, ge=0)
    min_forks: int = Field(10, ge=0)
    time_range: str = Field("weekly", regex="^(daily|weekly|monthly)$")
    include_readme: bool = True
    include_issues: bool = True
    include_discussions: bool = True
    max_issues_per_repo: int = Field(10, ge=0, le=50)
    viral_threshold_stars_per_day: int = Field(50, ge=1)
    exclude_archived: bool = True
    exclude_forks: bool = True


class ResearchScheduleRequest(BaseModel):
    frequency: str = Field(..., regex="^(daily|weekly|biweekly|monthly|custom)$")
    time_of_day: str = Field("09:00", regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = "UTC"
    days_of_week: Optional[List[int]] = Field(None, description="0=Monday, 6=Sunday")
    custom_cron: Optional[str] = None


class GitHubResearchConfigRequest(BaseModel):
    user_id: str = Field(..., example="user_001")
    workspace_id: str = Field(..., example="workspace_001")
    config_name: str = Field(..., example="trending_tech")
    description: str = Field(..., example="Daily GitHub research on trending technologies")

    github_config: GitHubConfigRequest
    analysis_depth: str = Field("standard", regex="^(basic|standard|comprehensive)$")
    ai_model: str = "gpt-5-mini"
    focus_areas: List[str] = Field(default_factory=lambda: ["technology_insights", "trend_analysis"])

    schedule: Optional[ResearchScheduleRequest] = None
    auto_run_enabled: bool = False
    generate_summary: bool = True
    generate_insights: bool = True
    generate_content_ideas: bool = True
    export_formats: List[str] = Field(default_factory=lambda: ["json", "markdown"])


class JobTriggerRequest(BaseModel):
    config_name: Optional[str] = None
    job_type: str = Field("pipeline", regex="^(raw|analyze|pipeline)$")
    priority: str = Field("normal", regex="^(low|normal|high)$")


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str  # running, completed, failed, queued
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    results_path: Optional[str] = None
    error_message: Optional[str] = None


# In-memory job tracking (use database in production)
active_jobs: Dict[str, JobStatusResponse] = {}
job_history: List[JobStatusResponse] = []


@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "GitHub Research API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "github_token_configured": bool(os.getenv("GITHUB_TOKEN")),
        "rate_limit": "5000/hour" if os.getenv("GITHUB_TOKEN") else "60/hour",
        "endpoints": {"configs": "/configs", "jobs": "/jobs", "health": "/health"},
    }


@app.post("/configs", response_model=Dict[str, Any])
async def create_research_config(request: GitHubResearchConfigRequest):
    """Create new GitHub research configuration"""
    try:
        # Convert request to config object
        github_config = GitHubConfig(
            content_types=[GitHubContentType(t) for t in request.github_config.content_types],
            search_topics=request.github_config.search_topics,
            languages=request.github_config.languages,
            max_repos_per_search=request.github_config.max_repos_per_search,
            min_stars=request.github_config.min_stars,
            min_forks=request.github_config.min_forks,
            time_range=GitHubTimeRange(request.github_config.time_range),
            include_readme=request.github_config.include_readme,
            include_issues=request.github_config.include_issues,
            include_discussions=request.github_config.include_discussions,
            max_issues_per_repo=request.github_config.max_issues_per_repo,
            viral_threshold_stars_per_day=request.github_config.viral_threshold_stars_per_day,
            exclude_archived=request.github_config.exclude_archived,
            exclude_forks=request.github_config.exclude_forks,
        )

        schedule = None
        if request.schedule:
            schedule = ResearchSchedule(
                frequency=ResearchFrequency(request.schedule.frequency),
                time_of_day=request.schedule.time_of_day,
                timezone=request.schedule.timezone,
                days_of_week=request.schedule.days_of_week,
                custom_cron=request.schedule.custom_cron,
            )

        config = GitHubResearchConfig(
            user_id=request.user_id,
            workspace_id=request.workspace_id,
            config_name=request.config_name,
            description=request.description,
            github_config=github_config,
            analysis_depth=AnalysisDepth(request.analysis_depth),
            ai_model=request.ai_model,
            focus_areas=request.focus_areas,
            schedule=schedule,
            auto_run_enabled=request.auto_run_enabled,
            generate_summary=request.generate_summary,
            generate_insights=request.generate_insights,
            generate_content_ideas=request.generate_content_ideas,
            export_formats=request.export_formats,
        )

        # Save configuration
        success = config_manager.create_config(config)

        if success:
            return {
                "success": True,
                "message": f"GitHub research configuration '{request.config_name}' created successfully",
                "config_id": f"{request.user_id}_{request.config_name}",
                "created_at": config.created_at,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create configuration")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/configs/{user_id}", response_model=List[str])
async def list_user_configs(user_id: str):
    """List user's GitHub configurations"""
    try:
        configs = config_manager.list_user_configs(user_id)
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/configs/{user_id}/{config_name}", response_model=Dict[str, Any])
async def get_research_config(user_id: str, config_name: str):
    """Get specific GitHub configuration"""
    try:
        config = config_manager.load_config(user_id, config_name)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Convert to dict for JSON response
        from dataclasses import asdict

        return asdict(config)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/configs/{user_id}/{config_name}", response_model=Dict[str, Any])
async def update_research_config(user_id: str, config_name: str, updates: Dict[str, Any]):
    """Update GitHub configuration"""
    try:
        success = config_manager.update_config(user_id, config_name, updates)

        if success:
            return {
                "success": True,
                "message": f"Configuration '{config_name}' updated successfully",
                "updated_at": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(status_code=404, detail="Configuration not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/configs/{user_id}/{config_name}", response_model=Dict[str, Any])
async def delete_research_config(user_id: str, config_name: str):
    """Delete GitHub configuration"""
    try:
        success = config_manager.delete_config(user_id, config_name)

        if success:
            return {
                "success": True,
                "message": f"Configuration '{config_name}' deleted successfully",
                "deleted_at": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(status_code=404, detail="Configuration not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/trigger", response_model=Dict[str, Any])
async def trigger_research_job(request: JobTriggerRequest, background_tasks: BackgroundTasks):
    """Manually trigger GitHub research job"""
    try:
        job_id = f"github_job_{int(datetime.now().timestamp())}"

        # Create job status
        job_status = JobStatusResponse(
            job_id=job_id, job_type=request.job_type, status="queued", started_at=datetime.now().isoformat()
        )

        active_jobs[job_id] = job_status

        # Start background job
        background_tasks.add_task(execute_research_job, job_id, request.job_type, request.config_name)

        return {
            "success": True,
            "job_id": job_id,
            "message": f"GitHub {request.job_type} job started",
            "status_url": f"/jobs/status/{job_id}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def execute_research_job(job_id: str, job_type: str, config_name: Optional[str]):
    """Execute GitHub research job in background"""
    job_status = active_jobs.get(job_id)
    if not job_status:
        return

    try:
        job_status.status = "running"

        # Get script directory
        script_dir = Path(__file__).parent
        runner_script = script_dir / "run_github_background.sh"

        # Execute appropriate job type
        if job_type == "raw":
            cmd = [str(runner_script), "raw"]
        elif job_type == "analyze":
            cmd = [str(runner_script), "analyze"]
        elif job_type == "pipeline":
            cmd = [str(runner_script), "pipeline"]
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        # Run command
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            job_status.status = "completed"
            job_status.completed_at = datetime.now().isoformat()

            # Try to find results
            if job_type in ["raw", "pipeline"]:
                raw_data_dir = script_dir / "raw_data"
                if raw_data_dir.exists():
                    latest_raw = max(raw_data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, default=None)
                    if latest_raw:
                        job_status.results_path = str(latest_raw)

            if job_type in ["analyze", "pipeline"]:
                analyzed_data_dir = script_dir / "analyzed_data"
                if analyzed_data_dir.exists():
                    latest_analyzed = max(
                        analyzed_data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, default=None
                    )
                    if latest_analyzed:
                        job_status.results_path = str(latest_analyzed)
        else:
            job_status.status = "failed"
            job_status.error_message = stderr.decode() if stderr else "Unknown error"
            job_status.completed_at = datetime.now().isoformat()

    except Exception as e:
        job_status.status = "failed"
        job_status.error_message = str(e)
        job_status.completed_at = datetime.now().isoformat()

    finally:
        # Move to history
        job_history.append(job_status)
        if job_id in active_jobs:
            del active_jobs[job_id]


@app.get("/jobs/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get GitHub job status"""
    # Check active jobs first
    if job_id in active_jobs:
        return active_jobs[job_id]

    # Check job history
    for job in job_history:
        if job.job_id == job_id:
            return job

    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/jobs/active", response_model=List[JobStatusResponse])
async def get_active_jobs():
    """Get all active GitHub jobs"""
    return list(active_jobs.values())


@app.get("/jobs/history", response_model=List[JobStatusResponse])
async def get_job_history(limit: int = 20):
    """Get GitHub job history"""
    # Sort by start time (most recent first)
    sorted_history = sorted(job_history, key=lambda x: x.started_at or "", reverse=True)
    return sorted_history[:limit]


@app.post("/jobs/trigger-direct", response_model=Dict[str, Any])
async def trigger_direct_research(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Direct trigger endpoint for orchestration API"""
    try:
        job_id = f"github_direct_{int(datetime.now().timestamp())}"

        # Extract job configuration
        job_type = request.get("job_type", "pipeline")
        user_id = request.get("user_id", "unknown")

        # Create job status
        job_status = JobStatusResponse(
            job_id=job_id, job_type=job_type, status="queued", started_at=datetime.now().isoformat()
        )

        active_jobs[job_id] = job_status

        # Start background job
        background_tasks.add_task(
            execute_research_job, job_id, job_type, None  # No specific config for direct triggers
        )

        return {
            "success": True,
            "job_id": job_id,
            "message": f"GitHub {job_type} job started",
            "results_url": f"/jobs/status/{job_id}",
            "metrics": {
                "estimated_duration": "8-15 minutes",
                "job_type": job_type,
                "rate_limit": "5000/hour" if os.getenv("GITHUB_TOKEN") else "60/hour",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Comprehensive health check"""

    script_dir = Path(__file__).parent

    health_status = {
        "service": "github_research_api",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len(active_jobs),
        "job_history_count": len(job_history),
        "github_token_configured": bool(os.getenv("GITHUB_TOKEN")),
        "rate_limit": "5000/hour" if os.getenv("GITHUB_TOKEN") else "60/hour",
        "directories": {
            "raw_data": (script_dir / "raw_data").exists(),
            "analyzed_data": (script_dir / "analyzed_data").exists(),
            "user_configs": (script_dir / "user_configs").exists(),
        },
    }

    # Check if background runner is available
    runner_script = script_dir / "run_github_background.sh"
    health_status["background_runner_available"] = runner_script.exists()

    # Test GitHub API connectivity
    try:
        from features.github_research.cli_github_scraper_raw import GitHubAPI

        test_api = GitHubAPI()
        test_repos = test_api.search_repositories("test", per_page=1)
        health_status["github_api_connectivity"] = "healthy" if test_repos is not None else "degraded"
        health_status["github_api_rate_limit_remaining"] = test_api.rate_limit_remaining
    except Exception as e:
        health_status["github_api_connectivity"] = "failed"
        health_status["github_api_error"] = str(e)

    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
