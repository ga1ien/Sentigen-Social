#!/usr/bin/env python3
"""
Google Trends Research API Service
FastAPI service for Google Trends research with user authentication
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from core.research_service import (
    JobStatus,
    JobType,
    ResearchConfiguration,
    ResearchJob,
    ResearchSource,
    research_service,
)
from core.user_auth import UserContext, get_current_user
from features.google_trends_research.google_trends_research_config import (
    AnalysisDepth,
    ContentOpportunityType,
    GoogleTrendsConfig,
    GoogleTrendsResearchConfig,
    GoogleTrendsResearchConfigManager,
    TrendsCategory,
    TrendsGeoLocation,
    TrendsTimeframe,
)

# Initialize FastAPI app
app = FastAPI(
    title="Google Trends Research API",
    description="User-accessible Google Trends research with content intelligence",
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
class CreateGoogleTrendsConfigRequest(BaseModel):
    config_name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    keywords: List[str] = Field(..., description="Keywords to analyze")
    timeframe: str = Field("now 7-d", description="Analysis timeframe")
    geo_location: str = Field("US", description="Geographic location")
    category: str = Field("0", description="Google Trends category")
    opportunity_types: List[str] = Field(
        ["breakout", "rising", "questions"], description="Types of opportunities to find"
    )
    analysis_depth: str = Field("standard", description="Analysis depth")
    include_youtube_trends: bool = Field(True, description="Include YouTube trends")
    include_news_trends: bool = Field(True, description="Include news trends")
    target_content_types: List[str] = Field(["blog", "social"], description="Target content types")
    auto_run_enabled: bool = Field(False, description="Enable automatic scheduling")
    workspace_id: Optional[str] = Field(None, description="Workspace ID (optional)")


class UpdateGoogleTrendsConfigRequest(BaseModel):
    config_name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    timeframe: Optional[str] = None
    geo_location: Optional[str] = None
    opportunity_types: Optional[List[str]] = None
    analysis_depth: Optional[str] = None
    include_youtube_trends: Optional[bool] = None
    auto_run_enabled: Optional[bool] = None


class GoogleTrendsJobRequest(BaseModel):
    configuration_id: str = Field(..., description="Configuration ID to run")
    job_type: str = Field("pipeline", description="Job type (raw, analyze, pipeline)")
    priority: str = Field("normal", description="Job priority")


class QuickTrendsRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to analyze")
    timeframe: str = Field("now 7-d", description="Analysis timeframe")
    geo_location: str = Field("US", description="Geographic location")


class GoogleTrendsConfigResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    config_name: str
    description: Optional[str]
    keywords: List[str]
    timeframe: str
    geo_location: str
    category: str
    opportunity_types: List[str]
    analysis_depth: str
    include_youtube_trends: bool
    include_news_trends: bool
    target_content_types: List[str]
    auto_run_enabled: bool
    is_active: bool
    created_at: str
    updated_at: str
    last_run_at: Optional[str]


class GoogleTrendsJobResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    configuration_id: Optional[str]
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


class QuickTrendsResponse(BaseModel):
    keywords: List[str]
    timeframe: str
    geo_location: str
    analysis: Dict[str, Any]
    opportunities: List[Dict[str, Any]]
    timestamp: str


# Initialize configuration manager
config_manager = GoogleTrendsResearchConfigManager()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""

    # Check if pytrends is available
    pytrends_available = False
    try:
        import pytrends

        pytrends_available = True
    except ImportError:
        pass

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "pytrends_available": pytrends_available,
        "service": "google_trends_research",
    }


# Configuration endpoints
@app.post("/configurations", response_model=GoogleTrendsConfigResponse)
async def create_configuration(
    request: CreateGoogleTrendsConfigRequest, user_context: UserContext = Depends(get_current_user)
):
    """Create a new Google Trends research configuration"""
    try:
        # Use provided workspace or default to first available
        workspace_id = request.workspace_id
        if not workspace_id and user_context.workspaces:
            workspace_id = user_context.workspaces[0]["id"]

        if not workspace_id:
            raise HTTPException(status_code=400, detail="No workspace available")

        # Create Google Trends specific configuration
        trends_config = GoogleTrendsConfig(
            keywords=request.keywords,
            timeframe=TrendsTimeframe(request.timeframe),
            geo_location=TrendsGeoLocation(request.geo_location),
            category=TrendsCategory(request.category),
            opportunity_types=[ContentOpportunityType(ot) for ot in request.opportunity_types],
            analysis_depth=AnalysisDepth(request.analysis_depth),
            include_youtube_trends=request.include_youtube_trends,
            include_news_trends=request.include_news_trends,
            target_content_types=request.target_content_types,
        )

        google_trends_config = GoogleTrendsResearchConfig(
            user_id=user_context.user_id,
            workspace_id=workspace_id,
            config_name=request.config_name,
            description=request.description,
            trends_config=trends_config,
            auto_run_enabled=request.auto_run_enabled,
        )

        # Save configuration
        config_path = config_manager.create_config(google_trends_config)

        # Also create in unified research service
        unified_config = ResearchConfiguration(
            id=None,
            user_id=user_context.user_id,
            workspace_id=workspace_id,
            source_type=ResearchSource.GITHUB,  # We'll need to add GOOGLE_TRENDS
            config_name=request.config_name,
            description=request.description,
            configuration={
                "keywords": request.keywords,
                "timeframe": request.timeframe,
                "geo_location": request.geo_location,
                "category": request.category,
                "opportunity_types": request.opportunity_types,
                "analysis_depth": request.analysis_depth,
                "include_youtube_trends": request.include_youtube_trends,
                "include_news_trends": request.include_news_trends,
                "target_content_types": request.target_content_types,
            },
            auto_run_enabled=request.auto_run_enabled,
        )

        created_config = await research_service.create_configuration(user_context, unified_config)

        if not created_config:
            raise HTTPException(status_code=500, detail="Failed to create configuration")

        return GoogleTrendsConfigResponse(
            id=created_config.id,
            user_id=google_trends_config.user_id,
            workspace_id=google_trends_config.workspace_id,
            config_name=google_trends_config.config_name,
            description=google_trends_config.description,
            keywords=google_trends_config.trends_config.keywords,
            timeframe=google_trends_config.trends_config.timeframe.value,
            geo_location=google_trends_config.trends_config.geo_location.value,
            category=google_trends_config.trends_config.category.value,
            opportunity_types=[ot.value for ot in google_trends_config.trends_config.opportunity_types],
            analysis_depth=google_trends_config.trends_config.analysis_depth.value,
            include_youtube_trends=google_trends_config.trends_config.include_youtube_trends,
            include_news_trends=google_trends_config.trends_config.include_news_trends,
            target_content_types=google_trends_config.trends_config.target_content_types,
            auto_run_enabled=google_trends_config.auto_run_enabled,
            is_active=True,
            created_at=google_trends_config.created_at,
            updated_at=google_trends_config.updated_at,
            last_run_at=google_trends_config.last_run_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/configurations", response_model=List[GoogleTrendsConfigResponse])
async def list_configurations(
    workspace_id: Optional[str] = None, user_context: UserContext = Depends(get_current_user)
):
    """List user's Google Trends research configurations"""
    try:
        # Get configurations from unified service
        configs = await research_service.get_user_configurations(user_context.user_id, workspace_id)

        # Filter for Google Trends configs (based on configuration content)
        trends_configs = []
        for config in configs:
            if "keywords" in config.configuration and "timeframe" in config.configuration:
                trends_configs.append(
                    GoogleTrendsConfigResponse(
                        id=config.id,
                        user_id=config.user_id,
                        workspace_id=config.workspace_id,
                        config_name=config.config_name,
                        description=config.description,
                        keywords=config.configuration.get("keywords", []),
                        timeframe=config.configuration.get("timeframe", "now 7-d"),
                        geo_location=config.configuration.get("geo_location", "US"),
                        category=config.configuration.get("category", "0"),
                        opportunity_types=config.configuration.get("opportunity_types", ["breakout"]),
                        analysis_depth=config.configuration.get("analysis_depth", "standard"),
                        include_youtube_trends=config.configuration.get("include_youtube_trends", True),
                        include_news_trends=config.configuration.get("include_news_trends", True),
                        target_content_types=config.configuration.get("target_content_types", ["blog"]),
                        auto_run_enabled=config.auto_run_enabled,
                        is_active=config.is_active,
                        created_at=config.created_at,
                        updated_at=config.updated_at,
                        last_run_at=config.last_run_at,
                    )
                )

        return trends_configs

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/configurations/{config_id}", response_model=GoogleTrendsConfigResponse)
async def get_configuration(config_id: str, user_context: UserContext = Depends(get_current_user)):
    """Get a specific Google Trends research configuration"""
    try:
        config = await research_service.get_configuration(config_id, user_context)

        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return GoogleTrendsConfigResponse(
            id=config.id,
            user_id=config.user_id,
            workspace_id=config.workspace_id,
            config_name=config.config_name,
            description=config.description,
            keywords=config.configuration.get("keywords", []),
            timeframe=config.configuration.get("timeframe", "now 7-d"),
            geo_location=config.configuration.get("geo_location", "US"),
            category=config.configuration.get("category", "0"),
            opportunity_types=config.configuration.get("opportunity_types", ["breakout"]),
            analysis_depth=config.configuration.get("analysis_depth", "standard"),
            include_youtube_trends=config.configuration.get("include_youtube_trends", True),
            include_news_trends=config.configuration.get("include_news_trends", True),
            target_content_types=config.configuration.get("target_content_types", ["blog"]),
            auto_run_enabled=config.auto_run_enabled,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            last_run_at=config.last_run_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/configurations/{config_id}", response_model=GoogleTrendsConfigResponse)
async def update_configuration(
    config_id: str, request: UpdateGoogleTrendsConfigRequest, user_context: UserContext = Depends(get_current_user)
):
    """Update a Google Trends research configuration"""
    try:
        # Get existing configuration
        existing_config = await research_service.get_configuration(config_id, user_context)
        if not existing_config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Prepare updates
        updates = {}
        if request.config_name is not None:
            updates["config_name"] = request.config_name
        if request.description is not None:
            updates["description"] = request.description
        if request.auto_run_enabled is not None:
            updates["auto_run_enabled"] = request.auto_run_enabled

        # Update configuration dictionary
        config_updates = {}
        if request.keywords is not None:
            config_updates["keywords"] = request.keywords
        if request.timeframe is not None:
            config_updates["timeframe"] = request.timeframe
        if request.geo_location is not None:
            config_updates["geo_location"] = request.geo_location
        if request.opportunity_types is not None:
            config_updates["opportunity_types"] = request.opportunity_types
        if request.analysis_depth is not None:
            config_updates["analysis_depth"] = request.analysis_depth
        if request.include_youtube_trends is not None:
            config_updates["include_youtube_trends"] = request.include_youtube_trends

        if config_updates:
            updated_configuration = existing_config.configuration.copy()
            updated_configuration.update(config_updates)
            updates["configuration"] = updated_configuration

        updated_config = await research_service.update_configuration(config_id, updates, user_context)

        if not updated_config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return GoogleTrendsConfigResponse(
            id=updated_config.id,
            user_id=updated_config.user_id,
            workspace_id=updated_config.workspace_id,
            config_name=updated_config.config_name,
            description=updated_config.description,
            keywords=updated_config.configuration.get("keywords", []),
            timeframe=updated_config.configuration.get("timeframe", "now 7-d"),
            geo_location=updated_config.configuration.get("geo_location", "US"),
            category=updated_config.configuration.get("category", "0"),
            opportunity_types=updated_config.configuration.get("opportunity_types", ["breakout"]),
            analysis_depth=updated_config.configuration.get("analysis_depth", "standard"),
            include_youtube_trends=updated_config.configuration.get("include_youtube_trends", True),
            include_news_trends=updated_config.configuration.get("include_news_trends", True),
            target_content_types=updated_config.configuration.get("target_content_types", ["blog"]),
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
    """Delete a Google Trends research configuration"""
    try:
        success = await research_service.delete_configuration(config_id, user_context)

        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return {"message": "Configuration deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Job endpoints
@app.post("/jobs", response_model=GoogleTrendsJobResponse)
async def create_job(
    request: GoogleTrendsJobRequest,
    background_tasks: BackgroundTasks,
    user_context: UserContext = Depends(get_current_user),
):
    """Create and start a Google Trends research job"""
    try:
        # Get configuration
        config = await research_service.get_configuration(request.configuration_id, user_context)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Create job
        job = ResearchJob(
            id=None,
            user_id=user_context.user_id,
            workspace_id=config.workspace_id,
            configuration_id=request.configuration_id,
            source_type=ResearchSource.GITHUB,  # We'll need to add GOOGLE_TRENDS
            job_type=JobType(request.job_type),
            status=JobStatus.QUEUED,
            priority=request.priority,
            metadata={"started_by": "api", "api_version": "1.0", "source": "google_trends"},
        )

        created_job = await research_service.create_job(user_context, job)

        if not created_job:
            raise HTTPException(status_code=500, detail="Failed to create job")

        # Add background task to execute the job
        background_tasks.add_task(execute_google_trends_job, created_job.id, config)

        return GoogleTrendsJobResponse(
            id=created_job.id,
            user_id=created_job.user_id,
            workspace_id=created_job.workspace_id,
            configuration_id=created_job.configuration_id,
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


@app.get("/jobs", response_model=List[GoogleTrendsJobResponse])
async def list_jobs(
    workspace_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    user_context: UserContext = Depends(get_current_user),
):
    """List user's Google Trends research jobs"""
    try:
        jobs = await research_service.get_user_jobs(user_context.user_id, workspace_id, limit)

        # Filter for Google Trends jobs
        trends_jobs = [j for j in jobs if j.metadata and j.metadata.get("source") == "google_trends"]

        # Filter by status if specified
        if status:
            trends_jobs = [j for j in trends_jobs if j.status.value == status]

        return [
            GoogleTrendsJobResponse(
                id=job.id,
                user_id=job.user_id,
                workspace_id=job.workspace_id,
                configuration_id=job.configuration_id,
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
            for job in trends_jobs
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=GoogleTrendsJobResponse)
async def get_job(job_id: str, user_context: UserContext = Depends(get_current_user)):
    """Get a specific Google Trends research job"""
    try:
        job = await research_service.get_job(job_id, user_context)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return GoogleTrendsJobResponse(
            id=job.id,
            user_id=job.user_id,
            workspace_id=job.workspace_id,
            configuration_id=job.configuration_id,
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


# Quick trends endpoint
@app.post("/quick-trends", response_model=QuickTrendsResponse)
async def quick_trends_analysis(request: QuickTrendsRequest, user_context: UserContext = Depends(get_current_user)):
    """Perform quick Google Trends analysis"""
    try:
        # Check if pytrends is available
        try:
            from pytrends.request import TrendReq
        except ImportError:
            raise HTTPException(status_code=503, detail="pytrends library not available")

        # Perform quick analysis
        pytrends = TrendReq(hl="en-US", tz=360)
        analysis_results = {}
        opportunities = []

        for keyword in request.keywords:
            try:
                pytrends.build_payload([keyword], timeframe=request.timeframe, geo=request.geo_location)
                interest = pytrends.interest_over_time()

                if not interest.empty:
                    current = int(interest[keyword].iloc[-1])
                    avg = float(interest[keyword].mean())
                    peak = int(interest[keyword].max())
                    trend = "rising" if current > avg else "falling"

                    analysis_results[keyword] = {
                        "current_interest": current,
                        "average_interest": avg,
                        "peak_interest": peak,
                        "trend": trend,
                        "volatility": float(interest[keyword].std()),
                    }

                    # Simple opportunity detection
                    if current > 50:
                        opportunities.append(
                            {
                                "keyword": keyword,
                                "opportunity_type": "high_interest",
                                "current_interest": current,
                                "recommendation": "Create content immediately",
                                "urgency": "HIGH",
                            }
                        )
                    elif trend == "rising" and current > 25:
                        opportunities.append(
                            {
                                "keyword": keyword,
                                "opportunity_type": "rising_trend",
                                "current_interest": current,
                                "recommendation": "Monitor and prepare content",
                                "urgency": "MEDIUM",
                            }
                        )

                # Small delay to avoid rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                analysis_results[keyword] = {"error": str(e)}

        return QuickTrendsResponse(
            keywords=request.keywords,
            timeframe=request.timeframe,
            geo_location=request.geo_location,
            analysis=analysis_results,
            opportunities=opportunities,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Background task to execute Google Trends jobs
async def execute_google_trends_job(job_id: str, config):
    """Execute a Google Trends research job in the background"""
    try:
        # Update job status to running
        await research_service.update_job_status(job_id, JobStatus.RUNNING)

        # Import and execute Google Trends research
        from features.google_trends_research.cli_google_trends_user_accessible import UserAccessibleGoogleTrendsCLI

        cli = UserAccessibleGoogleTrendsCLI()
        await cli.initialize(config.user_id)
        await cli.run_research_job(config.id, "pipeline")

        # Update job status to completed
        await research_service.update_job_status(job_id, JobStatus.COMPLETED)

    except Exception as e:
        # Update job status to failed
        await research_service.update_job_status(job_id, JobStatus.FAILED, error_message=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "google_trends_research_api:app",
        host="0.0.0.0",
        port=8004,  # Different port for Google Trends service
        reload=True,
    )
