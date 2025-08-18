"""
API endpoints for Research-to-Video workflow
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from orchestrator.research_to_video_workflow import (
    ResearchToVideoWorkflow, 
    WorkflowConfig, 
    WorkflowResult,
    WorkflowStatus,
    Platform
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/research-video", tags=["Research Video Workflow"])

# Lazy initialization to avoid import-time environment variable issues
_workflow_orchestrator = None

def get_workflow_orchestrator():
    """Get workflow orchestrator with lazy initialization."""
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        _workflow_orchestrator = ResearchToVideoWorkflow()
    return _workflow_orchestrator


# Request/Response Models
class StartWorkflowRequest(BaseModel):
    """Request to start research-to-video workflow"""
    research_topics: List[str] = Field(
        ..., 
        description="Topics to research (e.g., ['AI automation', 'productivity tools'])",
        min_items=1,
        max_items=5
    )
    platforms_to_research: List[str] = Field(
        default=["reddit", "twitter", "linkedin"],
        description="Platforms to research for content"
    )
    target_audience: str = Field(
        ...,
        description="Target audience for the video (e.g., 'tech entrepreneurs', 'developers')"
    )
    video_style: str = Field(
        default="professional",
        description="Video style: professional, casual, educational"
    )
    avatar_id: Optional[str] = Field(
        None,
        description="HeyGen avatar ID to use"
    )
    voice_id: Optional[str] = Field(
        None,
        description="HeyGen voice ID to use"
    )
    max_video_duration: int = Field(
        default=60,
        description="Maximum video duration in seconds",
        ge=15,
        le=180
    )
    auto_publish: bool = Field(
        default=False,
        description="Auto-publish without approval (use with caution)"
    )
    tiktok_hashtags: Optional[List[str]] = Field(
        None,
        description="Custom hashtags for TikTok post"
    )


class WorkflowStatusResponse(BaseModel):
    """Workflow status response"""
    workflow_id: str
    status: str
    progress: float = Field(description="Progress percentage (0-100)")
    current_step: str
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ApprovalRequest(BaseModel):
    """Request to approve/reject workflow"""
    approved: bool
    feedback: Optional[str] = Field(
        None,
        description="Optional feedback for rejection"
    )


class PendingApprovalResponse(BaseModel):
    """Pending approval response"""
    workflow_id: str
    script: str
    video_url: str
    video_metadata: Dict[str, Any]
    research_summary: Dict[str, Any]
    created_at: datetime
    config: Dict[str, Any]


@router.post("/start", response_model=Dict[str, str])
async def start_research_video_workflow(
    request: StartWorkflowRequest,
    background_tasks: BackgroundTasks,
    user_id: str = "default_user",  # TODO: Get from auth
    workspace_id: str = "default_workspace"  # TODO: Get from auth
):
    """
    Start a new research-to-video workflow
    
    This will:
    1. Research the specified topics across platforms
    2. Generate insights and trending topics
    3. Create a video script based on research
    4. Generate an AI video using HeyGen
    5. Either auto-publish or wait for approval
    """
    try:
        # Convert platform strings to Platform enums
        platforms = []
        for platform_str in request.platforms_to_research:
            try:
                platforms.append(Platform(platform_str.lower()))
            except ValueError:
                logger.warning("Invalid platform", platform=platform_str)
                continue
        
        if not platforms:
            raise HTTPException(
                status_code=400,
                detail="At least one valid platform must be specified"
            )
        
        # Create workflow config
        config = WorkflowConfig(
            research_topics=request.research_topics,
            platforms_to_research=platforms,
            target_audience=request.target_audience,
            video_style=request.video_style,
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            max_video_duration=request.max_video_duration,
            auto_publish=request.auto_publish,
            tiktok_hashtags=request.tiktok_hashtags
        )
        
        # Start workflow in background
        background_tasks.add_task(
            _execute_workflow_background,
            config,
            user_id,
            workspace_id
        )
        
        # Generate workflow ID for tracking
        workflow_id = f"rtv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("Research-to-video workflow started", 
                   workflow_id=workflow_id, 
                   topics=request.research_topics)
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Research-to-video workflow started successfully"
        }
        
    except Exception as e:
        logger.error("Failed to start workflow", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get the current status of a workflow"""
    try:
        status_data = await get_workflow_orchestrator().get_workflow_status(workflow_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Calculate progress based on status
        progress_map = {
            "pending": 0,
            "researching": 20,
            "analyzing": 40,
            "script_generation": 60,
            "video_generation": 80,
            "awaiting_approval": 90,
            "approved": 95,
            "publishing": 98,
            "completed": 100,
            "failed": 0,
            "cancelled": 0
        }
        
        progress = progress_map.get(status_data["status"], 0)
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=status_data["status"],
            progress=progress,
            current_step=status_data["status"].replace("_", " ").title(),
            error_message=status_data.get("error_message"),
            created_at=datetime.fromisoformat(status_data["created_at"]),
            updated_at=datetime.fromisoformat(status_data["updated_at"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending-approvals", response_model=List[PendingApprovalResponse])
async def get_pending_approvals(
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Get all workflows awaiting approval for the user"""
    try:
        pending_approvals = await get_workflow_orchestrator().list_pending_approvals(user_id)
        
        responses = []
        for approval in pending_approvals:
            approval_data = approval.get("workflow_approvals", [])
            if approval_data:
                approval_info = approval_data[0]
                responses.append(PendingApprovalResponse(
                    workflow_id=approval["id"],
                    script=approval_info["script"],
                    video_url=approval_info["video_result"]["video_url"],
                    video_metadata=approval_info["video_result"],
                    research_summary={
                        "topics": approval["workflow_config"]["research_topics"],
                        "platforms": approval["workflow_config"]["platforms_to_research"]
                    },
                    created_at=datetime.fromisoformat(approval_info["created_at"]),
                    config=approval_info["config"]
                ))
        
        return responses
        
    except Exception as e:
        logger.error("Failed to get pending approvals", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve/{workflow_id}", response_model=Dict[str, Any])
async def approve_workflow(
    workflow_id: str,
    request: ApprovalRequest
):
    """Approve or reject a workflow awaiting approval"""
    try:
        result = await get_workflow_orchestrator().approve_and_publish(
            workflow_id=workflow_id,
            approved=request.approved,
            user_feedback=request.feedback
        )
        
        return {
            "workflow_id": workflow_id,
            "approved": request.approved,
            "status": result.status.value,
            "published_post_ids": result.published_post_ids,
            "message": "Workflow approved and published" if request.approved else "Workflow rejected"
        }
        
    except Exception as e:
        logger.error("Failed to process approval", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows", response_model=List[Dict[str, Any]])
async def list_workflows(
    user_id: str = "default_user",  # TODO: Get from auth
    status: Optional[str] = None,
    limit: int = 20
):
    """List workflows for a user"""
    try:
        # TODO: Implement proper workflow listing from database
        # This is a placeholder implementation
        return []
        
    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow"""
    try:
        # TODO: Implement workflow cancellation
        await get_workflow_orchestrator()._update_workflow_status(
            workflow_id, 
            WorkflowStatus.CANCELLED
        )
        
        return {"message": "Workflow cancelled successfully"}
        
    except Exception as e:
        logger.error("Failed to cancel workflow", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for research-video workflow system"""
    try:
        # Check Chrome MCP connection
        chrome_healthy = await get_workflow_orchestrator().chrome_worker.health_check()
        
        # Check HeyGen connection
        heygen_healthy = get_workflow_orchestrator().video_worker.heygen_client is not None
        
        # Check Ayrshare connection
        ayrshare_healthy = await get_workflow_orchestrator().ayrshare_client.health_check()
        
        return {
            "status": "healthy",
            "components": {
                "chrome_mcp": chrome_healthy,
                "heygen": heygen_healthy,
                "ayrshare": ayrshare_healthy,
                "database": True  # TODO: Add DB health check
            },
            "workflow_orchestrator": "ready"
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Background task function
async def _execute_workflow_background(
    config: WorkflowConfig,
    user_id: str,
    workspace_id: str
):
    """Execute workflow in background"""
    try:
        result = await get_workflow_orchestrator().execute_workflow(
            config=config,
            user_id=user_id,
            workspace_id=workspace_id
        )
        
        logger.info("Background workflow completed", 
                   workflow_id=result.workflow_id,
                   status=result.status.value)
        
    except Exception as e:
        logger.error("Background workflow failed", error=str(e))


# Include router in main app
def include_research_video_routes(app):
    """Include research-video routes in the main app"""
    app.include_router(router)
