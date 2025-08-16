"""
Main FastAPI application for the AI Social Media Platform.
Follows the Project Server Standards v1.0.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sse_starlette.sse import EventSourceResponse
import structlog
from dotenv import load_dotenv

# Import models
from models_content import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    PostCreateRequest,
    PostUpdateRequest,
    PostResponse,
    PostListResponse,
    MediaUploadRequest,
    MediaAsset,
    WorkspaceCreateRequest,
    Workspace,
    APIResponse,
    Platform,
    PostStatus
)
from models_social_media import HealthCheckResponse

# Import agents and services
from agents.content_agent import ContentGenerationAgent
from agents.social_media_agent import SocialMediaAgent
from database.supabase_client import SupabaseClient
from utils.ayrshare_client import AyrshareClient
from utils.heygen_client import HeyGenClient
from workers.midjourney_worker import MidjourneyWorker
from services.content_intelligence_orchestrator import ContentIntelligenceOrchestrator

# Import API routes
from api.routes.content_intelligence import router as content_intelligence_router

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

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Social Media Platform API")
    
    # Initialize services
    try:
        # Database
        app.state.db = SupabaseClient()
        
        # Social media services
        app.state.ayrshare_client = AyrshareClient()
        
        # AI agents
        app.state.content_agent = ContentGenerationAgent()
        app.state.social_media_agent = SocialMediaAgent()
        
        # Optional services
        try:
            app.state.heygen_client = HeyGenClient()
            logger.info("HeyGen client initialized successfully")
        except ValueError:
            app.state.heygen_client = None
            logger.info("HeyGen client not initialized - API key not provided")
        
        try:
            app.state.midjourney_worker = MidjourneyWorker()
            logger.info("Midjourney worker initialized successfully")
        except Exception as e:
            app.state.midjourney_worker = None
            logger.info("Midjourney worker not initialized", error=str(e))
        
        # Content Intelligence Orchestrator
        try:
            app.state.content_intelligence = ContentIntelligenceOrchestrator(num_workers=3)
            logger.info("Content Intelligence Orchestrator initialized successfully")
        except Exception as e:
            app.state.content_intelligence = None
            logger.warning("Content Intelligence Orchestrator not initialized", error=str(e))
        
        # Test connections
        db_healthy = await app.state.db.health_check()
        ayrshare_healthy = await app.state.ayrshare_client.health_check()
        
        if db_healthy:
            logger.info("Database connection successful")
        else:
            logger.warning("Database connection failed")
        
        if ayrshare_healthy:
            logger.info("Ayrshare API connection successful")
        else:
            logger.warning("Ayrshare API connection failed")
            
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        # Continue startup even if external services fail
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Social Media Platform API")
    if hasattr(app.state, 'db'):
        await app.state.db.close()


# Create FastAPI app
app = FastAPI(
    title="AI Social Media Platform",
    description="AI-powered social media content creation and scheduling platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "https://127.0.0.1:3000"
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(content_intelligence_router)


# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    # In a real implementation, this would validate the JWT token
    # For now, we'll return a mock user
    return {
        "id": "user-123",
        "email": "user@example.com",
        "workspace_id": "workspace-123"
    }


async def get_db() -> SupabaseClient:
    """Get database client."""
    return app.state.db


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    db_connected = False
    ayrshare_connected = False
    heygen_connected = False
    midjourney_connected = False
    
    try:
        if hasattr(app.state, 'db'):
            db_connected = await app.state.db.health_check()
    except Exception as e:
        logger.warning("Health check failed for database", error=str(e))
    
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
            "database": db_connected,
            "ayrshare": ayrshare_connected,
            "heygen": heygen_connected,
            "midjourney": midjourney_connected,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY"))
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Social Media Platform API",
        "version": "1.0.0",
        "description": "AI-powered social media content creation and scheduling",
        "docs": "/docs",
        "health": "/health"
    }


# Content Generation Endpoints
@app.post("/api/content/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate AI-powered social media content."""
    logger.info("Generating content", user_id=current_user["id"], prompt=request.prompt[:100])
    
    try:
        content_agent = app.state.content_agent
        
        # Get brand context from user's workspace (mock for now)
        brand_context = {
            "brand_voice": "professional and engaging",
            "target_audience": "business professionals and entrepreneurs",
            "brand_guidelines": {
                "tone": request.tone,
                "avoid_topics": ["politics", "controversial subjects"],
                "preferred_hashtags": ["#innovation", "#business", "#growth"]
            }
        }
        
        response = await content_agent.generate_content(
            request=request,
            user_id=current_user["id"],
            workspace_id=current_user["workspace_id"],
            brand_context=brand_context
        )
        
        return response
        
    except Exception as e:
        logger.error("Content generation failed", user_id=current_user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@app.post("/api/content/optimize/{platform}")
async def optimize_content_for_platform(
    platform: Platform,
    content: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Optimize content for a specific platform."""
    logger.info("Optimizing content for platform", platform=platform.value, user_id=current_user["id"])
    
    try:
        content_agent = app.state.content_agent
        
        optimized_content = await content_agent.optimize_for_platform(
            content=content,
            platform=platform,
            user_id=current_user["id"],
            workspace_id=current_user["workspace_id"]
        )
        
        return {"optimized_content": optimized_content, "platform": platform.value}
        
    except Exception as e:
        logger.error("Content optimization failed", platform=platform.value, error=str(e))
        raise HTTPException(status_code=500, detail=f"Content optimization failed: {str(e)}")


# Post Management Endpoints
@app.post("/api/posts", response_model=PostResponse)
async def create_post(
    request: PostCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """Create a new social media post."""
    logger.info("Creating post", user_id=current_user["id"], platforms=request.platforms)
    
    try:
        # Create post data
        post_data = {
            "workspace_id": current_user["workspace_id"],
            "user_id": current_user["id"],
            "content": request.content,
            "content_type": request.content_type.value,
            "platforms": [p.value for p in request.platforms],
            "media_urls": [],  # Will be populated with media asset URLs
            "status": PostStatus.DRAFT.value,
            "scheduled_at": request.scheduled_at.isoformat() if request.scheduled_at else None,
            "tags": request.tags,
            "campaign_id": str(request.campaign_id) if request.campaign_id else None,
            "metadata": {}
        }
        
        # Save to database
        created_post = await db.create_post(post_data)
        
        if not created_post:
            raise HTTPException(status_code=500, detail="Failed to create post")
        
        # Convert to response model (simplified for now)
        from models_content import SocialMediaPost
        post = SocialMediaPost(**created_post)
        
        return PostResponse(post=post, media_assets=[])
        
    except Exception as e:
        logger.error("Post creation failed", user_id=current_user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Post creation failed: {str(e)}")


@app.get("/api/posts", response_model=PostListResponse)
async def list_posts(
    page: int = 1,
    per_page: int = 20,
    status: Optional[PostStatus] = None,
    platform: Optional[Platform] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """List posts for the current user's workspace."""
    logger.info("Listing posts", user_id=current_user["id"], page=page, per_page=per_page)
    
    try:
        # Get posts from database
        posts = await db.get_workspace_posts(
            workspace_id=current_user["workspace_id"],
            limit=per_page
        )
        
        # Convert to response models (simplified)
        from models_content import SocialMediaPost
        post_models = []
        for post_data in posts:
            try:
                post = SocialMediaPost(**post_data)
                post_models.append(post)
            except Exception as e:
                logger.warning("Failed to parse post", post_id=post_data.get("id"), error=str(e))
                continue
        
        return PostListResponse(
            posts=post_models,
            total=len(post_models),
            page=page,
            per_page=per_page,
            has_next=len(post_models) == per_page
        )
        
    except Exception as e:
        logger.error("Post listing failed", user_id=current_user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Post listing failed: {str(e)}")


@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """Get a specific post by ID."""
    logger.info("Getting post", post_id=str(post_id), user_id=current_user["id"])
    
    try:
        post_data = await db.get_post(str(post_id))
        
        if not post_data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Verify user has access to this post
        if post_data.get("workspace_id") != current_user["workspace_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        from models_content import SocialMediaPost
        post = SocialMediaPost(**post_data)
        
        return PostResponse(post=post, media_assets=[])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get post failed", post_id=str(post_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get post: {str(e)}")


@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    request: PostUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """Update a post."""
    logger.info("Updating post", post_id=str(post_id), user_id=current_user["id"])
    
    try:
        # Get existing post
        existing_post = await db.get_post(str(post_id))
        if not existing_post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Verify access
        if existing_post.get("workspace_id") != current_user["workspace_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = {}
        if request.content is not None:
            update_data["content"] = request.content
        if request.platforms is not None:
            update_data["platforms"] = [p.value for p in request.platforms]
        if request.scheduled_at is not None:
            update_data["scheduled_at"] = request.scheduled_at.isoformat()
        if request.status is not None:
            update_data["status"] = request.status.value
        if request.tags is not None:
            update_data["tags"] = request.tags
        
        # Update in database
        updated_post = await db.update_post(str(post_id), update_data)
        
        if not updated_post:
            raise HTTPException(status_code=500, detail="Failed to update post")
        
        from models_content import SocialMediaPost
        post = SocialMediaPost(**updated_post)
        
        return PostResponse(post=post, media_assets=[])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Post update failed", post_id=str(post_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Post update failed: {str(e)}")


@app.delete("/api/posts/{post_id}")
async def delete_post(
    post_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """Delete a post."""
    logger.info("Deleting post", post_id=str(post_id), user_id=current_user["id"])
    
    try:
        # Get existing post
        existing_post = await db.get_post(str(post_id))
        if not existing_post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Verify access
        if existing_post.get("workspace_id") != current_user["workspace_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete from database
        success = await db.delete_record("social_media_posts", str(post_id))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete post")
        
        return {"message": "Post deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Post deletion failed", post_id=str(post_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Post deletion failed: {str(e)}")


# Media Upload Endpoints
@app.post("/api/media/upload", response_model=MediaAsset)
async def upload_media(
    file: UploadFile = File(...),
    alt_text: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """Upload a media file."""
    logger.info("Uploading media", filename=file.filename, user_id=current_user["id"])
    
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "video/mp4", "video/webm"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Read file content
        content = await file.read()
        
        # In a real implementation, you would:
        # 1. Upload to cloud storage (S3, Cloudinary, etc.)
        # 2. Generate thumbnails for videos
        # 3. Extract metadata (dimensions, duration, etc.)
        
        # For now, we'll create a mock media asset
        media_data = {
            "workspace_id": current_user["workspace_id"],
            "user_id": current_user["id"],
            "filename": file.filename,
            "original_filename": file.filename,
            "file_type": file.content_type,
            "file_size": len(content),
            "storage_url": f"https://example.com/media/{file.filename}",  # Mock URL
            "alt_text": alt_text,
            "metadata": {}
        }
        
        created_asset = await db.create_media_asset(media_data)
        
        if not created_asset:
            raise HTTPException(status_code=500, detail="Failed to create media asset")
        
        media_asset = MediaAsset(**created_asset)
        return media_asset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Media upload failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Media upload failed: {str(e)}")


@app.get("/api/media", response_model=List[MediaAsset])
async def list_media(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """List media assets for the current workspace."""
    logger.info("Listing media", user_id=current_user["id"])
    
    try:
        media_data = await db.get_workspace_media(current_user["workspace_id"])
        
        media_assets = []
        for asset_data in media_data:
            try:
                asset = MediaAsset(**asset_data)
                media_assets.append(asset)
            except Exception as e:
                logger.warning("Failed to parse media asset", asset_id=asset_data.get("id"), error=str(e))
                continue
        
        return media_assets
        
    except Exception as e:
        logger.error("Media listing failed", user_id=current_user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Media listing failed: {str(e)}")


# Publishing Endpoints
@app.post("/api/posts/{post_id}/publish")
async def publish_post(
    post_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Publish a post to social media platforms."""
    logger.info("Publishing post", post_id=str(post_id), user_id=current_user["id"])
    
    try:
        # Get post
        post_data = await db.get_post(str(post_id))
        if not post_data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Verify access
        if post_data.get("workspace_id") != current_user["workspace_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if post is ready to publish
        if post_data.get("status") not in ["draft", "scheduled"]:
            raise HTTPException(status_code=400, detail="Post cannot be published")
        
        # Add background task to publish
        background_tasks.add_task(
            publish_post_background,
            post_id=str(post_id),
            post_data=post_data,
            db=db
        )
        
        # Update status to publishing
        await db.update_post(str(post_id), {"status": "publishing"})
        
        return {"message": "Post is being published", "post_id": str(post_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Post publishing failed", post_id=str(post_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Post publishing failed: {str(e)}")


async def publish_post_background(post_id: str, post_data: Dict[str, Any], db: SupabaseClient):
    """Background task to publish post to social media platforms."""
    try:
        # Use Ayrshare to publish
        ayrshare_client = app.state.ayrshare_client
        
        publish_data = {
            "post": post_data["content"],
            "platforms": post_data["platforms"],
            "mediaUrls": post_data.get("media_urls", [])
        }
        
        result = await ayrshare_client.post_content(publish_data)
        
        # Update post with results
        update_data = {
            "status": "published" if result.get("success") else "failed",
            "published_at": datetime.utcnow().isoformat(),
            "platform_results": result,
            "ayrshare_post_id": result.get("id")
        }
        
        await db.update_post(post_id, update_data)
        
        logger.info("Post published successfully", post_id=post_id)
        
    except Exception as e:
        logger.error("Background post publishing failed", post_id=post_id, error=str(e))
        
        # Update post status to failed
        await db.update_post(post_id, {
            "status": "failed",
            "metadata": {"error": str(e)}
        })


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=True if os.getenv("APP_ENV") == "development" else False
    )
