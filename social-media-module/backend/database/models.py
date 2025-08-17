"""
Database models for the social media module.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


class UserRole(str, Enum):
    """User roles."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class TaskStatus(str, Enum):
    """Task status options."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PostStatus(str, Enum):
    """Post status options."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class MediaType(str, Enum):
    """Media asset types."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class WorkerType(str, Enum):
    """Worker types."""

    RESEARCH = "research"
    CONTENT = "content"
    TOOL = "tool"
    IMAGE = "image"
    AVATAR_VIDEO = "avatar_video"
    VIDEO = "video"


class SubscriptionTier(str, Enum):
    """Subscription tier options."""

    FREE = "free"
    STARTER = "starter"
    CREATOR = "creator"
    CREATOR_PRO = "creator_pro"
    ENTERPRISE = "enterprise"


class User(BaseModel):
    """User model - enhanced to match unified schema."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    role: UserRole = UserRole.USER
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    is_admin: bool = False
    is_active: bool = True
    onboarding_completed: bool = False
    preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class Workspace(BaseModel):
    """Workspace model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    owner_id: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    brand_guidelines: Optional[Dict[str, Any]] = None
    social_accounts: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class SocialMediaPost(BaseModel):
    """Social media post model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    title: Optional[str] = None
    content: str
    platforms: List[str]
    media_assets: List[str] = Field(default_factory=list)  # Media asset IDs
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    status: PostStatus = PostStatus.DRAFT
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None
    platform_results: List[Dict[str, Any]] = Field(default_factory=list)
    analytics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class WorkerTask(BaseModel):
    """Worker task model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    worker_type: WorkerType
    task_type: str
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class WorkerResult(BaseModel):
    """Worker result model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    worker_type: WorkerType
    status: str  # success, error, partial
    result_data: Any
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class MediaAsset(BaseModel):
    """Media asset model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    filename: str
    original_filename: str
    media_type: MediaType
    file_size: int
    mime_type: str
    url: HttpUrl
    thumbnail_url: Optional[HttpUrl] = None
    dimensions: Optional[Dict[str, int]] = None  # width, height
    duration: Optional[float] = None  # for video/audio
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class Campaign(BaseModel):
    """Marketing campaign model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    objectives: List[str] = Field(default_factory=list)
    target_audience: Dict[str, Any] = Field(default_factory=dict)
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    posts: List[str] = Field(default_factory=list)  # Post IDs
    status: str = "draft"
    analytics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentTemplate(BaseModel):
    """Content template model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    category: str
    template_content: str
    variables: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    usage_count: int = 0
    is_public: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowExecution(BaseModel):
    """Workflow execution model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    workflow_name: str
    workflow_config: Dict[str, Any]
    tasks: List[str] = Field(default_factory=list)  # Task IDs
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


# =====================================================
# ADDITIONAL MODELS FOR UNIFIED SCHEMA
# =====================================================


class WorkspaceMember(BaseModel):
    """Workspace member model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    role: str = "member"  # owner, admin, editor, member
    permissions: Dict[str, Any] = Field(default_factory=dict)
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class SocialPlatform(BaseModel):
    """Social platform model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: str
    icon_url: Optional[str] = None
    api_config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserSocialAccount(BaseModel):
    """User social account model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    workspace_id: str
    platform_id: str
    account_name: str
    account_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    account_metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None


class ContentPost(BaseModel):
    """Content post model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    title: Optional[str] = None
    content: str
    content_type: str = "text"  # text, image, video, carousel, story
    status: str = "draft"  # draft, scheduled, published, failed, archived
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchConfiguration(BaseModel):
    """Research configuration model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    workspace_id: str
    source_type: str  # reddit, hackernews, github, google_trends, linkedin, twitter
    config_name: str
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    schedule: Dict[str, Any] = Field(default_factory=dict)
    auto_run_enabled: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_run_at: Optional[datetime] = None


class ResearchJob(BaseModel):
    """Research job model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    workspace_id: str
    configuration_id: Optional[str] = None
    source_type: str
    job_type: str = "pipeline"  # raw, analyze, pipeline
    status: str = "queued"  # queued, running, completed, failed, cancelled
    priority: str = "normal"  # low, normal, high
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    results_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchResult(BaseModel):
    """Research result model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    workspace_id: str
    job_id: str
    source_type: str
    result_type: str = "analysis"  # raw, analysis, insights
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    insights: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False
    quality_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentEmbedding(BaseModel):
    """Content embedding model for vector search."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    content_type: str
    content_id: str
    content_text: str
    embedding: List[float]  # Vector embedding
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AnalyticsEvent(BaseModel):
    """Analytics event model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: Optional[str] = None
    event_type: str
    event_data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# NOTE: Database schema is now unified at /database/complete_supabase_schema.sql
# This file contains Pydantic models that match the unified database schema
