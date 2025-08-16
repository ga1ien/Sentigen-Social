"""
Database models for the social media module.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
import uuid


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


class User(BaseModel):
    """User model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
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


# Database schema creation SQL
DATABASE_SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}',
    brand_guidelines JSONB,
    social_accounts JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Social media posts table
CREATE TABLE IF NOT EXISTS social_media_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    content TEXT NOT NULL,
    platforms TEXT[] DEFAULT '{}',
    media_assets TEXT[] DEFAULT '{}',
    hashtags TEXT[] DEFAULT '{}',
    mentions TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft',
    scheduled_for TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    platform_results JSONB DEFAULT '[]',
    analytics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Worker tasks table
CREATE TABLE IF NOT EXISTS worker_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    worker_type VARCHAR(50) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 300,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Worker results table
CREATE TABLE IF NOT EXISTS worker_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES worker_tasks(id) ON DELETE CASCADE,
    worker_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    result_data JSONB,
    error_message TEXT,
    execution_time FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Media assets table
CREATE TABLE IF NOT EXISTS media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    media_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    dimensions JSONB,
    duration FLOAT,
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    objectives TEXT[] DEFAULT '{}',
    target_audience JSONB DEFAULT '{}',
    budget DECIMAL(10,2),
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    posts TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft',
    analytics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content templates table
CREATE TABLE IF NOT EXISTS content_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    template_content TEXT NOT NULL,
    variables TEXT[] DEFAULT '{}',
    platforms TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    usage_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_config JSONB NOT NULL,
    tasks TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '{}',
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_workspaces_owner_id ON workspaces(owner_id);
CREATE INDEX IF NOT EXISTS idx_posts_workspace_id ON social_media_posts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON social_media_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON social_media_posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_scheduled_for ON social_media_posts(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_tasks_workspace_id ON worker_tasks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON worker_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_worker_type ON worker_tasks(worker_type);
CREATE INDEX IF NOT EXISTS idx_results_task_id ON worker_results(task_id);
CREATE INDEX IF NOT EXISTS idx_media_workspace_id ON media_assets(workspace_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_workspace_id ON campaigns(workspace_id);
CREATE INDEX IF NOT EXISTS idx_templates_workspace_id ON content_templates(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workflows_workspace_id ON workflow_executions(workspace_id);

-- Updated at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON social_media_posts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON worker_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_media_updated_at BEFORE UPDATE ON media_assets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON content_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflow_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""