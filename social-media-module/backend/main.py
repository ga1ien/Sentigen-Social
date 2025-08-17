"""
FastAPI application for social media posting module.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
import structlog
from dotenv import load_dotenv

from models_social_media import (
    SocialMediaPostRequest,
    SocialMediaPostResponse,
    SocialMediaAnalyticsRequest,
    SocialMediaAnalyticsResponse,
    HealthCheckResponse,
    PostStatus,
    PlatformResult
)
from agents.social_media_agent import SocialMediaAgent, SocialMediaAgentDeps
from utils.ayrshare_client import AyrshareClient
from utils.heygen_client import HeyGenClient
from workers.midjourney_worker import MidjourneyWorker
from api.research_video_api import router as research_video_router
from api.avatar_api import router as avatar_router

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting social media posting API")
    
    # Initialize clients
    try:
        ayrshare_client = AyrshareClient()
        app.state.ayrshare_client = ayrshare_client
        
        # Initialize HeyGen client if API key is available
        try:
            heygen_client = HeyGenClient()
            app.state.heygen_client = heygen_client
            logger.info("HeyGen client initialized successfully")
        except ValueError:
            app.state.heygen_client = None
            logger.info("HeyGen client not initialized - API key not provided")
        
        app.state.social_media_agent = SocialMediaAgent()
        
        # Test Ayrshare connection
        is_healthy = await ayrshare_client.health_check()
        if is_healthy:
            logger.info("Ayrshare API connection successful")
        else:
            logger.warning("Ayrshare API connection failed - check API key")
        
        # Test HeyGen connection if client exists
        if app.state.heygen_client:
            heygen_healthy = await app.state.heygen_client.health_check()
            if heygen_healthy:
                logger.info("HeyGen API connection successful")
            else:
                logger.warning("HeyGen API connection failed - check API key")
        
        # Initialize Midjourney worker if API key is available
        try:
            midjourney_worker = MidjourneyWorker()
            app.state.midjourney_worker = midjourney_worker
            
            # Test Midjourney connection
            midjourney_healthy = await midjourney_worker.health_check()
            if midjourney_healthy:
                logger.info("Midjourney worker initialized and connected successfully")
            else:
                logger.warning("Midjourney worker initialized but connection failed - check CometAPI key")
        except Exception as e:
            app.state.midjourney_worker = None
            logger.info("Midjourney worker not initialized", error=str(e))
            
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        # Continue startup even if external services fail
    
    yield
    
    # Shutdown
    logger.info("Shutting down social media posting API")


# Create FastAPI app
app = FastAPI(
    title="Social Media Posting API",
    description="AI-powered social media posting module using Ayrshare",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
# Get CORS origins from environment variable, fallback to wildcard for development
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include research-video workflow routes
app.include_router(research_video_router)
app.include_router(avatar_router)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Social Media Posting API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    ayrshare_connected = False
    heygen_connected = False
    midjourney_connected = False
    
    try:
        if hasattr(app.state, 'ayrshare_client'):
            ayrshare_connected = await app.state.ayrshare_client.health_check()
    except Exception as e:
        logger.warning("Health check failed for Ayrshare", error=str(e))
    
    try:
        if hasattr(app.state, 'heygen_client') and app.state.heygen_client:
            heygen_connected = await app.state.heygen_client.health_check()
    except Exception as e:
        logger.warning("Health check failed for HeyGen", error=str(e))
    
    try:
        if hasattr(app.state, 'midjourney_worker') and app.state.midjourney_worker:
            midjourney_connected = await app.state.midjourney_worker.health_check()
    except Exception as e:
        logger.warning("Health check failed for Midjourney", error=str(e))
    
    return HealthCheckResponse(
        status="healthy",
        ayrshare_connected=ayrshare_connected,
        heygen_connected=heygen_connected,
        services={
            "ayrshare": ayrshare_connected,
            "heygen": heygen_connected,
            "midjourney": midjourney_connected,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),
            "cometapi": bool(os.getenv("COMETAPI_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY"))
        }
    )


@app.post("/api/post", response_model=SocialMediaPostResponse)
async def create_social_media_post(
    request: SocialMediaPostRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a social media post across multiple platforms.
    """
    logger.info("Creating social media post", platforms=request.platforms)
    
    try:
        # Get the agent from app state
        if not hasattr(app.state, 'social_media_agent'):
            raise HTTPException(
                status_code=500,
                detail="Social media agent not initialized"
            )
        
        agent = app.state.social_media_agent
        
        # Build the prompt for the agent
        prompt_parts = []
        
        if request.random_post:
            prompt_parts.append("Please create a random test post")
        else:
            prompt_parts.append(f"Please post the following content: '{request.post}'")
        
        prompt_parts.append(f"to the following platforms: {', '.join(request.platforms)}")
        
        if request.media_urls:
            prompt_parts.append(f"Include these media URLs: {', '.join(map(str, request.media_urls))}")
        elif request.random_media_url:
            prompt_parts.append("Include a random test image")
        
        if request.is_portrait_video:
            prompt_parts.append("Use portrait video format")
        elif request.is_landscape_video:
            prompt_parts.append("Use landscape video format")
        
        if request.schedule_date:
            prompt_parts.append(f"Schedule the post for: {request.schedule_date.isoformat()}")
        
        if request.hashtags:
            prompt_parts.append(f"Include these hashtags: {', '.join(request.hashtags)}")
        
        if request.mentions:
            prompt_parts.append(f"Mention these users: {', '.join(request.mentions)}")
        
        prompt = ". ".join(prompt_parts) + "."
        
        # Create context
        context = "You are helping a user post content to their connected social media accounts."
        
        # Run the agent
        result = await agent.post_content(
            prompt=prompt,
            context=context,
            workspace_metadata={}
        )
        
        # Convert agent result to API response
        if result.status == "success":
            # Parse platform results if they exist
            platform_results = []
            if result.platform_results:
                for platform_result in result.platform_results:
                    if isinstance(platform_result, dict):
                        platform_results.append(PlatformResult(
                            platform=platform_result.get("platform", "unknown"),
                            status=PostStatus.SUCCESS if platform_result.get("status") == "success" else PostStatus.ERROR,
                            post_id=platform_result.get("id"),
                            post_url=platform_result.get("postUrl"),
                            error_message=platform_result.get("errorMessage"),
                            used_quota=platform_result.get("usedQuota"),
                            additional_info=platform_result
                        ))
            
            response = SocialMediaPostResponse(
                status=PostStatus.SUCCESS,
                message=result.message or "Post created successfully",
                post_id=result.post_id,
                ref_id=result.ref_id,
                post_content=result.post_content or request.post,
                platform_results=platform_results,
                errors=result.errors or [],
                scheduled_for=request.schedule_date
            )
        else:
            response = SocialMediaPostResponse(
                status=PostStatus.ERROR,
                message=result.message or "Failed to create post",
                errors=result.errors or ["Unknown error occurred"],
                scheduled_for=request.schedule_date
            )
        
        logger.info("Social media post completed", 
                   status=response.status,
                   platforms=request.platforms)
        
        return response
        
    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to create social media post", error=error_msg)
        
        return SocialMediaPostResponse(
            status=PostStatus.ERROR,
            message=f"Failed to create post: {error_msg}",
            errors=[error_msg]
        )


@app.post("/api/post/stream")
async def create_social_media_post_stream(request: SocialMediaPostRequest):
    """
    Create a social media post with streaming response.
    """
    async def generate_events():
        try:
            yield {
                "event": "status",
                "data": json.dumps({"status": "starting", "message": "Initializing post creation..."})
            }
            
            # Get the agent
            if not hasattr(app.state, 'social_media_agent'):
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Social media agent not initialized"})
                }
                return
            
            agent = app.state.social_media_agent
            
            yield {
                "event": "status", 
                "data": json.dumps({"status": "processing", "message": "Creating post content..."})
            }
            
            # Build prompt (same logic as above)
            prompt_parts = []
            
            if request.random_post:
                prompt_parts.append("Please create a random test post")
            else:
                prompt_parts.append(f"Please post the following content: '{request.post}'")
            
            prompt_parts.append(f"to the following platforms: {', '.join(request.platforms)}")
            
            if request.media_urls:
                prompt_parts.append(f"Include these media URLs: {', '.join(map(str, request.media_urls))}")
            elif request.random_media_url:
                prompt_parts.append("Include a random test image")
            
            prompt = ". ".join(prompt_parts) + "."
            
            yield {
                "event": "status",
                "data": json.dumps({"status": "posting", "message": "Posting to social media platforms..."})
            }
            
            # Run the agent
            result = await agent.post_content(
                prompt=prompt,
                context="You are helping a user post content to their connected social media accounts."
            )
            
            if result.status == "success":
                yield {
                    "event": "success",
                    "data": json.dumps({
                        "status": "completed",
                        "message": result.message,
                        "post_id": result.post_id,
                        "platform_results": result.platform_results
                    })
                }
            else:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "status": "failed",
                        "message": result.message,
                        "errors": result.errors
                    })
                }
                
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(generate_events())


@app.get("/api/analytics/{post_id}", response_model=SocialMediaAnalyticsResponse)
async def get_post_analytics(post_id: str):
    """
    Get analytics for a specific post.
    """
    logger.info("Getting post analytics", post_id=post_id)
    
    try:
        if not hasattr(app.state, 'ayrshare_client'):
            raise HTTPException(
                status_code=500,
                detail="Ayrshare client not initialized"
            )
        
        client = app.state.ayrshare_client
        analytics_data = await client.get_post_analytics(post_id)
        
        return SocialMediaAnalyticsResponse(
            post_id=post_id,
            analytics=analytics_data
        )
        
    except Exception as e:
        logger.error("Failed to get post analytics", error=str(e), post_id=post_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics: {str(e)}"
        )


@app.get("/api/accounts")
async def get_connected_accounts():
    """
    Get connected social media accounts.
    """
    logger.info("Getting connected accounts")
    
    try:
        if not hasattr(app.state, 'ayrshare_client'):
            raise HTTPException(
                status_code=500,
                detail="Ayrshare client not initialized"
            )
        
        client = app.state.ayrshare_client
        accounts = await client.get_connected_accounts()
        
        return accounts
        
    except Exception as e:
        logger.error("Failed to get connected accounts", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get connected accounts: {str(e)}"
        )


@app.post("/api/optimize")
async def optimize_content(
    content: str,
    platforms: list[str],
    include_hashtags: bool = True,
    include_mentions: bool = True
):
    """
    Optimize content for specific social media platforms.
    """
    logger.info("Optimizing content", platforms=platforms)
    
    try:
        if not hasattr(app.state, 'social_media_agent'):
            raise HTTPException(
                status_code=500,
                detail="Social media agent not initialized"
            )
        
        agent = app.state.social_media_agent
        
        # Create a simple prompt for optimization
        prompt = f"""
        Please optimize this content for the platforms {', '.join(platforms)}:
        
        "{content}"
        
        Include hashtag suggestions: {include_hashtags}
        Include mention suggestions: {include_mentions}
        """
        
        result = await agent.post_content(
            prompt=prompt,
            context="You are helping optimize content for different social media platforms."
        )
        
        return {
            "status": "success",
            "original_content": content,
            "optimized_suggestions": result.message,
            "platforms": platforms
        }
        
    except Exception as e:
        logger.error("Failed to optimize content", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize content: {str(e)}"
        )


@app.post("/api/heygen/video")
async def create_heygen_video(
    script: str,
    avatar_id: Optional[str] = None,
    voice_id: Optional[str] = None,
    background: Optional[str] = None
):
    """
    Create a video using HeyGen API.
    """
    logger.info("Creating HeyGen video", script_length=len(script))
    
    try:
        if not hasattr(app.state, 'heygen_client') or not app.state.heygen_client:
            raise HTTPException(
                status_code=503,
                detail="HeyGen service not available. Please configure HEYGEN_API_KEY."
            )
        
        client = app.state.heygen_client
        result = await client.create_video(
            script=script,
            avatar_id=avatar_id,
            voice_id=voice_id,
            background=background
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to create HeyGen video", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create video: {str(e)}"
        )


@app.get("/api/heygen/video/{video_id}")
async def get_heygen_video_status(video_id: str):
    """
    Get the status of a HeyGen video generation.
    """
    logger.info("Getting HeyGen video status", video_id=video_id)
    
    try:
        if not hasattr(app.state, 'heygen_client') or not app.state.heygen_client:
            raise HTTPException(
                status_code=503,
                detail="HeyGen service not available"
            )
        
        client = app.state.heygen_client
        result = await client.get_video_status(video_id)
        
        return result
        
    except Exception as e:
        logger.error("Failed to get HeyGen video status", error=str(e), video_id=video_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video status: {str(e)}"
        )


@app.get("/api/heygen/avatars")
async def list_heygen_avatars():
    """
    Get list of available HeyGen avatars.
    """
    logger.info("Getting HeyGen avatars")
    
    try:
        if not hasattr(app.state, 'heygen_client') or not app.state.heygen_client:
            raise HTTPException(
                status_code=503,
                detail="HeyGen service not available"
            )
        
        client = app.state.heygen_client
        result = await client.list_avatars()
        
        return result
        
    except Exception as e:
        logger.error("Failed to get HeyGen avatars", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get avatars: {str(e)}"
        )


@app.get("/api/heygen/voices")
async def list_heygen_voices():
    """
    Get list of available HeyGen voices.
    """
    logger.info("Getting HeyGen voices")
    
    try:
        if not hasattr(app.state, 'heygen_client') or not app.state.heygen_client:
            raise HTTPException(
                status_code=503,
                detail="HeyGen service not available"
            )
        
        client = app.state.heygen_client
        result = await client.list_voices()
        
        return result
        
    except Exception as e:
        logger.error("Failed to get HeyGen voices", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get voices: {str(e)}"
        )


# Midjourney API Endpoints

@app.post("/api/midjourney/image")
async def create_midjourney_image(
    prompt: str,
    aspect_ratio: Optional[str] = "1:1",
    style: Optional[str] = "photorealistic",
    quality: Optional[str] = "standard"
):
    """
    Generate an image using Midjourney via CometAPI.
    
    Args:
        prompt: Text description of the image to generate
        aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, etc.)
        style: Style preset (photorealistic, artistic, anime, cinematic, minimalist)
        quality: Quality level (standard, high, ultra)
    """
    logger.info("Creating Midjourney image", prompt=prompt[:100])
    
    try:
        if not hasattr(app.state, 'midjourney_worker') or not app.state.midjourney_worker:
            raise HTTPException(
                status_code=503,
                detail="Midjourney service not available"
            )
        
        worker = app.state.midjourney_worker
        
        # Create worker task
        from workers.base_worker import WorkerTask
        task = WorkerTask(
            task_id=f"mj_img_{datetime.utcnow().timestamp()}",
            worker_type="midjourney_worker",
            input_data={
                "type": "image",
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "style": style,
                "quality": quality
            }
        )
        
        result = await worker.process_task(task)
        
        if result.status == "error":
            raise HTTPException(
                status_code=500,
                detail=result.error_message
            )
        
        return result.result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create Midjourney image", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image: {str(e)}"
        )


@app.post("/api/midjourney/video")
async def create_midjourney_video(
    prompt: str,
    source_image: Optional[str] = None,
    video_type: Optional[str] = "vid_1.1_i2v_480",
    motion: Optional[str] = "low",
    animate_mode: Optional[str] = "manual"
):
    """
    Generate a video using Midjourney via CometAPI.
    
    Args:
        prompt: Text description for the video animation
        source_image: URL or base64 of source image (optional)
        video_type: Video generation type
        motion: Motion level (low, medium, high)
        animate_mode: Animation mode (manual, auto)
    """
    logger.info("Creating Midjourney video", prompt=prompt[:100])
    
    try:
        if not hasattr(app.state, 'midjourney_worker') or not app.state.midjourney_worker:
            raise HTTPException(
                status_code=503,
                detail="Midjourney service not available"
            )
        
        worker = app.state.midjourney_worker
        
        # Create worker task
        from workers.base_worker import WorkerTask
        task = WorkerTask(
            task_id=f"mj_vid_{datetime.utcnow().timestamp()}",
            worker_type="midjourney_worker",
            input_data={
                "type": "video",
                "prompt": prompt,
                "source_image": source_image,
                "video_type": video_type,
                "motion": motion,
                "animate_mode": animate_mode
            }
        )
        
        result = await worker.process_task(task)
        
        if result.status == "error":
            raise HTTPException(
                status_code=500,
                detail=result.error_message
            )
        
        return result.result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create Midjourney video", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate video: {str(e)}"
        )


@app.get("/api/midjourney/task/{task_id}")
async def get_midjourney_task_status(task_id: str):
    """
    Get the status of a Midjourney task.
    
    Args:
        task_id: The Midjourney task ID
    """
    logger.info("Getting Midjourney task status", task_id=task_id)
    
    try:
        if not hasattr(app.state, 'midjourney_worker') or not app.state.midjourney_worker:
            raise HTTPException(
                status_code=503,
                detail="Midjourney service not available"
            )
        
        worker = app.state.midjourney_worker
        result = await worker.get_task_status(task_id)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get Midjourney task status", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@app.post("/api/midjourney/upscale/{task_id}")
async def upscale_midjourney_image(task_id: str, index: int):
    """
    Upscale a specific image from a Midjourney generation.
    
    Args:
        task_id: Original Midjourney task ID
        index: Image index to upscale (1-4)
    """
    logger.info("Upscaling Midjourney image", task_id=task_id, index=index)
    
    try:
        if not hasattr(app.state, 'midjourney_worker') or not app.state.midjourney_worker:
            raise HTTPException(
                status_code=503,
                detail="Midjourney service not available"
            )
        
        if index < 1 or index > 4:
            raise HTTPException(
                status_code=400,
                detail="Index must be between 1 and 4"
            )
        
        worker = app.state.midjourney_worker
        result = await worker.upscale_image(task_id, index)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found or upscale failed"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upscale Midjourney image", task_id=task_id, index=index, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upscale image: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=True if os.getenv("APP_ENV") == "development" else False
    )