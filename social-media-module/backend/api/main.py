"""
Main FastAPI application for the AI Social Media Platform.
Follows the Project Server Standards v1.0.
"""

# Ensure /app is in sys.path for absolute imports when running under different cwd
import os as _os
import sys as _sys

if "/app" not in _sys.path:
    _sys.path.insert(0, "/app")

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sse_starlette.sse import EventSourceResponse

# Import routers using absolute package paths to avoid relative import issues
from api.avatar_api import router as avatar_router

# Import API routes
from api.content_research_api import router as content_research_router
from api.gpt5_auth_endpoint import router as gpt5_auth_router
from api.media_storage_api import router as media_storage_router
from api.research_tools_api import router as research_tools_router
from api.research_video_api import router as research_video_router
from api.social_accounts_api import router as social_accounts_router
from api.social_posting_api import router as social_posting_router
from core.cache_manager import CacheConfig, get_cache_manager, initialize_cache
from core.db_optimizer import get_connection_optimizer, get_db_optimizer

# Load and validate configuration
from core.env_config import AppConfig, get_config
from core.response_optimizer import PaginatedResponse, PaginationParams, get_response_optimizer

try:
    from database.supabase_client import SupabaseClient
except ModuleNotFoundError:
    from core.supabase_client import SupabaseClient

# Import models
from models.content import (
    APIResponse,
    ContentGenerationRequest,
    ContentGenerationResponse,
    MediaAsset,
    MediaUploadRequest,
    Platform,
    PostCreateRequest,
    PostListResponse,
    PostResponse,
    PostStatus,
    PostUpdateRequest,
    Workspace,
    WorkspaceCreateRequest,
)
from models.social_media import HealthCheckResponse, PlatformResult
from models.social_media import PostStatus as SocialMediaPostStatus
from models.social_media import (
    SocialMediaAnalyticsRequest,
    SocialMediaAnalyticsResponse,
    SocialMediaPostRequest,
    SocialMediaPostResponse,
)
from utils.ayrshare_client import AyrshareClient
from utils.heygen_client import HeyGenClient
from workers.midjourney_worker import MidjourneyWorker

# Import agents and services
# Temporarily disabled to debug environment variables
# from agents.content_agent import ContentGenerationAgent
# from agents.social_media_agent import SocialMediaAgent


# Lazy initialization to avoid import-time environment variable issues
_app_config = None


def get_app_config():
    """Get app config with lazy initialization."""
    global _app_config
    if _app_config is None:
        _app_config = get_config()
    return _app_config


# Initialize performance optimizations
cache_config = CacheConfig(
    redis_url=None, default_ttl=300, max_memory_cache_size=1000  # Will use in-memory cache for now
)
cache_manager = initialize_cache(cache_config)

# Configure structured logging with default settings (will be reconfigured after app startup)
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
        structlog.processors.JSONRenderer(),
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

    # Configure application with environment variables (now available)
    try:
        config = get_app_config()

        # Reconfigure logging with proper log level
        log_level = config.server.log_level.value.upper()
        import logging

        logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
        logger.info("Application configured", log_level=log_level, environment=config.server.environment.value)

    except Exception as e:
        logger.warning("Failed to load full configuration, using defaults", error=str(e))

    # Initialize services
    try:
        # Database
        app.state.db = SupabaseClient()

        # Social media services
        try:
            app.state.ayrshare_client = AyrshareClient()
        except Exception as e:
            app.state.ayrshare_client = None
            logger.info("Ayrshare client not initialized", error=str(e))

        # AI agents
        try:
            # Import agents only after environment is available
            from agents.content_agent import ContentGenerationAgent
            from agents.social_media_agent import SocialMediaAgent

            app.state.content_agent = ContentGenerationAgent()
            app.state.social_media_agent = SocialMediaAgent()
            logger.info("AI agents initialized successfully")
        except Exception as e:
            app.state.content_agent = None
            app.state.social_media_agent = None
            logger.info("AI agents not initialized", error=str(e))

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

        # Initialize cache manager
        try:
            await cache_manager.initialize()
            logger.info("Cache manager initialized successfully")
        except Exception as e:
            logger.warning("Cache manager initialization failed", error=str(e))

        # Content Intelligence Orchestrator
        try:
            # Temporarily disabled - needs refactoring to use new scrapers
            # app.state.content_intelligence = ContentIntelligenceOrchestrator(num_workers=3)
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
    if hasattr(app.state, "db"):
        await app.state.db.close()


# Create FastAPI app
app = FastAPI(
    title="AI Social Media Platform",
    description="AI-powered social media content creation and scheduling platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be configured properly after startup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(avatar_router)
app.include_router(research_video_router)
app.include_router(social_accounts_router)
app.include_router(social_posting_router)
app.include_router(content_research_router)
app.include_router(media_storage_router)
app.include_router(research_tools_router)
app.include_router(gpt5_auth_router, prefix="/api")


# Import authentication service
from core.user_auth import UserContext
from core.user_auth import get_current_user as auth_get_current_user


# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserContext:
    """Get current authenticated user with real JWT validation."""
    return await auth_get_current_user(credentials)


async def get_db() -> SupabaseClient:
    """Get database client."""
    return app.state.db


# Debug endpoints for authentication troubleshooting
@app.get("/debug/auth-flow")
async def debug_auth_flow(authorization: str = Header(None)):
    """Step-by-step authentication debugging per AI recommendations"""
    import os
    import traceback
    from datetime import datetime

    import jwt

    debug_info = {"timestamp": datetime.now().isoformat(), "step": "start", "success": False, "error": None}

    try:
        # Step 1: Check Authorization header
        debug_info["step"] = "header_check"
        if not authorization:
            debug_info["error"] = "No Authorization header present"
            return JSONResponse(content=debug_info, status_code=400)

        if not authorization.startswith("Bearer "):
            debug_info["error"] = "Authorization header doesn't start with 'Bearer '"
            return JSONResponse(content=debug_info, status_code=400)

        token = authorization.split(" ")[1]
        debug_info["token_length"] = len(token)
        debug_info["token_prefix"] = token[:20] + "..."

        # Step 2: JWT Decode
        debug_info["step"] = "jwt_decode"
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            debug_info["jwt_decode_success"] = True
            debug_info["user_id"] = decoded.get("sub")
            debug_info["email"] = decoded.get("email")
            debug_info["exp"] = decoded.get("exp")
            debug_info["iss"] = decoded.get("iss")
        except Exception as e:
            debug_info["jwt_decode_error"] = str(e)
            return JSONResponse(content=debug_info, status_code=400)

        # Step 3: Environment Variables
        debug_info["step"] = "env_check"
        debug_info["supabase_url"] = os.getenv("SUPABASE_URL")
        debug_info["has_service_key"] = bool(os.getenv("SUPABASE_SERVICE_KEY"))
        service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        debug_info["service_key_length"] = len(service_key)
        if service_key:
            debug_info["service_key_prefix"] = service_key[:30] + "..."
            debug_info["service_key_suffix"] = "..." + service_key[-10:]

        # Step 4: Supabase Client Test
        debug_info["step"] = "supabase_client_test"
        from supabase import create_client

        from core.supabase_client import SupabaseClient

        try:
            client = SupabaseClient()
            debug_info["supabase_client_created"] = True
        except Exception as e:
            debug_info["supabase_client_error"] = str(e)
            return JSONResponse(content=debug_info, status_code=500)

        # Step 5: Admin API Test
        debug_info["step"] = "admin_api_test"
        user_id = decoded.get("sub")
        try:
            admin_response = client.service_client.auth.admin.get_user_by_id(user_id)
            debug_info["admin_api_success"] = True
            debug_info["user_found"] = bool(admin_response.user)
            if admin_response.user:
                debug_info["verified_email"] = admin_response.user.email
            debug_info["success"] = True
        except Exception as e:
            debug_info["admin_api_error"] = str(e)
            debug_info["admin_api_traceback"] = traceback.format_exc()

        return JSONResponse(content=debug_info, status_code=200)

    except Exception as e:
        debug_info["unexpected_error"] = str(e)
        debug_info["traceback"] = traceback.format_exc()
        return JSONResponse(content=debug_info, status_code=500)


@app.get("/debug/supabase-connection")
async def debug_supabase_connection():
    """Test Supabase Admin API connectivity (Gemini's recommendation)"""
    import os
    import traceback
    from datetime import datetime

    from gotrue.errors import APIError as GotrueApiError

    debug_info = {"timestamp": datetime.now().isoformat()}

    try:
        from supabase import create_client

        from core.supabase_client import SupabaseClient

        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_KEY")

        debug_info["env_vars"] = {
            "supabase_url_present": bool(supabase_url),
            "service_key_present": bool(service_key),
            "service_key_length": len(service_key) if service_key else 0,
        }

        # Test 1: Client creation
        try:
            client = SupabaseClient()
            debug_info["client_creation"] = {"success": True}
        except Exception as e:
            debug_info["client_creation"] = {"success": False, "error": str(e)}
            return JSONResponse(content=debug_info, status_code=500)

        # Test 2: Admin API call with known user
        try:
            test_user_id = "6ec57fe0-6ffe-4662-9a17-20311fe525f5"  # Your user ID
            admin_response = client.service_client.auth.admin.get_user_by_id(test_user_id)
            debug_info["admin_api_test"] = {
                "success": True,
                "user_found": bool(admin_response.user),
                "user_email": admin_response.user.email if admin_response.user else None,
            }
        except GotrueApiError as e:
            debug_info["admin_api_test"] = {
                "success": False,
                "gotrue_error": str(e),
                "error_message": getattr(e, "message", str(e)),
                "error_status": getattr(e, "status", "unknown"),
            }
        except Exception as e:
            debug_info["admin_api_test"] = {
                "success": False,
                "unexpected_error": str(e),
                "traceback": traceback.format_exc(),
            }

        return JSONResponse(content=debug_info, status_code=200)

    except Exception as e:
        debug_info["unexpected_error"] = str(e)
        debug_info["traceback"] = traceback.format_exc()
        return JSONResponse(content=debug_info, status_code=500)


@app.get("/debug/alternative-auth")
async def debug_alternative_auth(authorization: str = Header(None)):
    """Test GPT-5's alternative auth method using direct Supabase API"""
    import os
    from datetime import datetime

    import httpx

    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "No valid Authorization header"}

    token = authorization.split(" ")[1]
    results = {"timestamp": datetime.now().isoformat()}

    # GPT-5's recommended method: Direct Supabase auth API
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        anon_key = os.getenv("SUPABASE_ANON_KEY")

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "apikey": anon_key,
                "Accept": "application/json",
            }

            response = await client.get(f"{supabase_url}/auth/v1/user", headers=headers)

            if response.status_code == 200:
                user_data = response.json()
                results["direct_api_method"] = {
                    "success": True,
                    "user_id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "status_code": response.status_code,
                }
            else:
                results["direct_api_method"] = {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                }

    except Exception as e:
        results["direct_api_method"] = {"success": False, "error": str(e)}

    return results


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)  # Force deploy v2.1
async def health_check():
    """Health check endpoint."""
    db_connected = False
    ayrshare_connected = False
    heygen_connected = False
    midjourney_connected = False

    try:
        if hasattr(app.state, "db"):
            db_connected = await app.state.db.health_check()
    except Exception as e:
        logger.warning("Health check failed for database", error=str(e))

    try:
        if hasattr(app.state, "ayrshare_client"):
            ayrshare_connected = await app.state.ayrshare_client.health_check()
    except Exception as e:
        logger.warning("Health check failed for Ayrshare", error=str(e))

    try:
        if hasattr(app.state, "heygen_client") and app.state.heygen_client:
            heygen_connected = await app.state.heygen_client.health_check()
    except Exception as e:
        logger.warning("Health check failed for HeyGen", error=str(e))

    try:
        if hasattr(app.state, "midjourney_worker") and app.state.midjourney_worker:
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
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
        },
    )


@app.get("/api/auth/me")
async def get_current_user_info(current_user: UserContext = Depends(get_current_user)):
    """Get current authenticated user information - test endpoint for auth integration."""
    logger.info("User info requested", user_id=current_user.user_id)

    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "subscription_tier": current_user.subscription_tier,
        "is_admin": current_user.is_admin,
        "workspaces": current_user.workspaces,
        "permissions": current_user.permissions,
        "auth_status": "authenticated",
    }


# Performance metrics endpoint
@app.get("/performance", response_model=Dict[str, Any])
async def performance_metrics():
    """Get performance metrics and statistics."""
    try:
        cache_manager = get_cache_manager()
        db_optimizer = get_db_optimizer()
        connection_optimizer = get_connection_optimizer()
        response_optimizer = get_response_optimizer()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache": cache_manager.get_stats() if cache_manager else {"status": "not_initialized"},
            "database": {
                "query_performance": db_optimizer.get_performance_report(),
                "connection_health": connection_optimizer.monitor_connection_health(),
                "optimization_suggestions": db_optimizer.optimize_suggestions(),
            },
            "responses": response_optimizer.get_stats(),
            "system": {
                "environment": get_app_config().server.environment.value,
                "log_level": get_app_config().server.log_level.value,
            },
        }
    except Exception as e:
        logger.error("Performance metrics failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Social Media Platform API",
        "version": "1.0.0",
        "description": "AI-powered social media content creation and scheduling",
        "docs": "/docs",
        "health": "/health",
        "performance": "/performance",
    }


# Content Generation Endpoints
@app.post("/api/content/generate", response_model=ContentGenerationResponse)
async def generate_content(request: ContentGenerationRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
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
                "preferred_hashtags": ["#innovation", "#business", "#growth"],
            },
        }

        response = await content_agent.generate_content(
            request=request,
            user_id=current_user["id"],
            workspace_id=current_user["workspace_id"],
            brand_context=brand_context,
        )

        return response

    except Exception as e:
        logger.error("Content generation failed", user_id=current_user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@app.post("/api/content/optimize/{platform}")
async def optimize_content_for_platform(
    platform: Platform, content: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Optimize content for a specific platform."""
    logger.info("Optimizing content for platform", platform=platform.value, user_id=current_user["id"])

    try:
        content_agent = app.state.content_agent

        optimized_content = await content_agent.optimize_for_platform(
            content=content, platform=platform, user_id=current_user["id"], workspace_id=current_user["workspace_id"]
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
    db: SupabaseClient = Depends(get_db),
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
            "metadata": {},
        }

        # Save to database
        created_post = await db.create_post(post_data)

        if not created_post:
            raise HTTPException(status_code=500, detail="Failed to create post")

        # Convert to response model (simplified for now)
        from models.content import SocialMediaPost

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
    db: SupabaseClient = Depends(get_db),
):
    """List posts for the current user's workspace."""
    logger.info("Listing posts", user_id=current_user["id"], page=page, per_page=per_page)

    try:
        # Get posts from database
        posts = await db.get_workspace_posts(workspace_id=current_user["workspace_id"], limit=per_page)

        # Convert to response models (simplified)
        from models.content import SocialMediaPost

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
            has_next=len(post_models) == per_page,
        )

    except Exception as e:
        logger.error("Post listing failed", user_id=current_user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Post listing failed: {str(e)}")


@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID, current_user: Dict[str, Any] = Depends(get_current_user), db: SupabaseClient = Depends(get_db)
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

        from models.content import SocialMediaPost

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
    db: SupabaseClient = Depends(get_db),
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

        from models.content import SocialMediaPost

        post = SocialMediaPost(**updated_post)

        return PostResponse(post=post, media_assets=[])

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Post update failed", post_id=str(post_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Post update failed: {str(e)}")


@app.delete("/api/posts/{post_id}")
async def delete_post(
    post_id: UUID, current_user: Dict[str, Any] = Depends(get_current_user), db: SupabaseClient = Depends(get_db)
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
    db: SupabaseClient = Depends(get_db),
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
            "metadata": {},
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
async def list_media(current_user: Dict[str, Any] = Depends(get_current_user), db: SupabaseClient = Depends(get_db)):
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
    background_tasks: BackgroundTasks = BackgroundTasks(),
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
        background_tasks.add_task(publish_post_background, post_id=str(post_id), post_data=post_data, db=db)

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
            "mediaUrls": post_data.get("media_urls", []),
        }

        result = await ayrshare_client.post_content(publish_data)

        # Update post with results
        update_data = {
            "status": "published" if result.get("success") else "failed",
            "published_at": datetime.utcnow().isoformat(),
            "platform_results": result,
            "ayrshare_post_id": result.get("id"),
        }

        await db.update_post(post_id, update_data)

        logger.info("Post published successfully", post_id=post_id)

    except Exception as e:
        logger.error("Background post publishing failed", post_id=post_id, error=str(e))

        # Update post status to failed
        await db.update_post(post_id, {"status": "failed", "metadata": {"error": str(e)}})


# ============================================================================
# LEGACY ENDPOINTS (from archived main.py) - for backward compatibility
# ============================================================================


@app.post("/api/post", response_model=SocialMediaPostResponse)
async def create_social_media_post_legacy(request: SocialMediaPostRequest, background_tasks: BackgroundTasks):
    """
    Legacy endpoint: Create a social media post across multiple platforms.
    This endpoint maintains backward compatibility with the old API.
    """
    logger.info("Creating social media post (legacy endpoint)", platforms=request.platforms)

    try:
        # Get the agent from app state
        if not hasattr(app.state, "social_media_agent"):
            raise HTTPException(status_code=500, detail="Social media agent not initialized")

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
        result = await agent.post_content(prompt=prompt, context=context, workspace_metadata={})

        # Convert agent result to API response
        if result.status == "success":
            return SocialMediaPostResponse(
                status="success",
                message=result.message,
                platform_results=result.platform_results,
                ayrshare_response=result.platform_results,
            )
        else:
            return SocialMediaPostResponse(
                status="error", message=result.message, platform_results=result.platform_results
            )

    except Exception as e:
        logger.error("Social media post creation failed", error=str(e))
        return SocialMediaPostResponse(status="error", message=f"Failed to create post: {str(e)}", platform_results={})


@app.post("/api/optimize")
async def optimize_content_legacy(
    content: str, platforms: list[str], include_hashtags: bool = True, include_mentions: bool = True
):
    """
    Legacy endpoint: Optimize content for specific platforms.
    """
    logger.info("Optimizing content for platforms", platforms=platforms)

    try:
        if not hasattr(app.state, "social_media_agent"):
            raise HTTPException(status_code=500, detail="Social media agent not initialized")

        agent = app.state.social_media_agent

        # Build optimization prompt
        prompt = f"Optimize this content for {', '.join(platforms)}: '{content}'"

        if include_hashtags:
            prompt += " Include relevant hashtags."
        if include_mentions:
            prompt += " Include relevant mentions where appropriate."

        # Use the agent to optimize content
        result = await agent.post_content(
            prompt=prompt, context="You are helping optimize content for social media platforms.", workspace_metadata={}
        )

        return {
            "status": "success",
            "optimized_content": result.message,
            "platforms": platforms,
            "original_content": content,
        }

    except Exception as e:
        logger.error("Content optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to optimize content: {str(e)}")


# HeyGen API Endpoints
@app.post("/api/heygen/video")
async def create_heygen_video(
    script: str, avatar_id: Optional[str] = None, voice_id: Optional[str] = None, background: Optional[str] = None
):
    """
    Create a video using HeyGen API.
    """
    logger.info("Creating HeyGen video", script_length=len(script))

    try:
        if not hasattr(app.state, "heygen_client") or not app.state.heygen_client:
            raise HTTPException(
                status_code=503, detail="HeyGen service not available. Please configure HEYGEN_API_KEY."
            )

        client = app.state.heygen_client
        result = await client.create_video(script=script, avatar_id=avatar_id, voice_id=voice_id, background=background)

        return result

    except Exception as e:
        logger.error("Failed to create HeyGen video", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}")


@app.get("/api/heygen/video/{video_id}")
async def get_heygen_video_status(video_id: str):
    """
    Get the status of a HeyGen video generation.
    """
    logger.info("Getting HeyGen video status", video_id=video_id)

    try:
        if not hasattr(app.state, "heygen_client") or not app.state.heygen_client:
            raise HTTPException(
                status_code=503, detail="HeyGen service not available. Please configure HEYGEN_API_KEY."
            )

        client = app.state.heygen_client
        result = await client.get_video_status(video_id)

        return result

    except Exception as e:
        logger.error("Failed to get HeyGen video status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get video status: {str(e)}")


@app.get("/api/heygen/avatars")
async def list_heygen_avatars():
    """
    List available HeyGen avatars.
    """
    logger.info("Listing HeyGen avatars")

    try:
        if not hasattr(app.state, "heygen_client") or not app.state.heygen_client:
            raise HTTPException(
                status_code=503, detail="HeyGen service not available. Please configure HEYGEN_API_KEY."
            )

        client = app.state.heygen_client
        result = await client.list_avatars()

        return result

    except Exception as e:
        logger.error("Failed to get HeyGen avatars", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get avatars: {str(e)}")


@app.get("/api/heygen/voices")
async def list_heygen_voices():
    """
    List available HeyGen voices.
    """
    logger.info("Listing HeyGen voices")

    try:
        if not hasattr(app.state, "heygen_client") or not app.state.heygen_client:
            raise HTTPException(
                status_code=503, detail="HeyGen service not available. Please configure HEYGEN_API_KEY."
            )

        client = app.state.heygen_client
        result = await client.list_voices()

        return result

    except Exception as e:
        logger.error("Failed to get HeyGen voices", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


# Midjourney API Endpoints
@app.post("/api/midjourney/image")
async def create_midjourney_image(
    prompt: str,
    aspect_ratio: Optional[str] = "1:1",
    style: Optional[str] = "photorealistic",
    quality: Optional[str] = "standard",
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
        if not hasattr(app.state, "midjourney_worker") or not app.state.midjourney_worker:
            raise HTTPException(status_code=503, detail="Midjourney service not available")

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
                "quality": quality,
            },
        )

        result = await worker.process_task(task)

        if result.status == "error":
            raise HTTPException(status_code=500, detail=result.error_message)

        return result.result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create Midjourney image", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")


@app.post("/api/midjourney/video")
async def create_midjourney_video(
    prompt: str,
    source_image: Optional[str] = None,
    video_type: Optional[str] = "vid_1.1_i2v_480",
    motion: Optional[str] = "low",
    animate_mode: Optional[str] = "manual",
):
    """
    Generate a video using Midjourney via CometAPI.
    """
    logger.info("Creating Midjourney video", prompt=prompt[:100])

    try:
        if not hasattr(app.state, "midjourney_worker") or not app.state.midjourney_worker:
            raise HTTPException(status_code=503, detail="Midjourney service not available")

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
                "animate_mode": animate_mode,
            },
        )

        result = await worker.process_task(task)

        if result.status == "error":
            raise HTTPException(status_code=500, detail=result.error_message)

        return result.result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create Midjourney video", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Use configuration for server settings
    uvicorn.run(
        "api.main:app",
        host=get_app_config().server.host,
        port=get_app_config().server.port,
        reload=get_app_config().server.environment.value == "development",
        log_level=get_app_config().server.log_level.value,
    )
