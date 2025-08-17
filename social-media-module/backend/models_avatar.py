"""
Avatar and Video Generation Models for Sentigen Social
Flattened version for Railway deployment
Integrated from TikClip functionality
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class AvatarType(str, Enum):
    """Types of avatars available"""
    TALKING_PHOTO = "talking_photo"
    AVATAR = "avatar"
    CUSTOM = "custom"


class VideoStatus(str, Enum):
    """Video generation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AspectRatio(str, Enum):
    """Video aspect ratios"""
    LANDSCAPE = "landscape"  # 16:9
    PORTRAIT = "portrait"    # 9:16 (TikTok/Instagram Stories)
    SQUARE = "square"        # 1:1 (Instagram posts)


class SubscriptionTier(str, Enum):
    """User subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    CREATOR = "creator"
    CREATOR_PRO = "creator_pro"
    ENTERPRISE = "enterprise"


# Pydantic Models for API
class AvatarProfile(BaseModel):
    """Avatar profile model"""
    id: Optional[int] = None
    name: str = Field(..., description="Display name for the avatar")
    avatar_id: str = Field(..., description="HeyGen avatar ID")
    voice_id: str = Field(..., description="HeyGen voice ID")
    display_order: int = Field(default=0, description="Order for display in UI")
    is_default: bool = Field(default=False, description="Whether this is the default avatar")
    description: Optional[str] = Field(None, description="Avatar description")
    preview_url: Optional[str] = Field(None, description="Preview video/image URL")
    avatar_type: AvatarType = Field(default=AvatarType.TALKING_PHOTO, description="Type of avatar")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class ScriptGeneration(BaseModel):
    """Script generation model"""
    id: Optional[int] = None
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    topic: str = Field(..., max_length=120, description="Topic for the script")
    script: str = Field(..., description="Generated script content")
    target_audience: Optional[str] = Field(None, description="Target audience")
    video_style: Optional[str] = Field(None, description="Video style (professional, casual, etc.)")
    duration_target: Optional[int] = Field(None, description="Target duration in seconds")
    model_used: Optional[str] = Field(None, description="AI model used for generation")
    quality_score: Optional[float] = Field(None, description="Quality score (0-1)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class VideoGeneration(BaseModel):
    """Video generation model"""
    id: Optional[int] = None
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    script_id: Optional[int] = Field(None, description="Associated script ID")
    profile_id: Optional[int] = Field(None, description="Avatar profile ID used")
    heygen_video_id: str = Field(..., description="HeyGen video generation ID")
    video_url: Optional[str] = Field(None, description="Final video URL")
    thumbnail_url: Optional[str] = Field(None, description="Video thumbnail URL")
    status: VideoStatus = Field(default=VideoStatus.PENDING, description="Generation status")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.LANDSCAPE, description="Video aspect ratio")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    avatar_id: Optional[str] = Field(None, description="HeyGen avatar ID (for backward compatibility)")
    voice_id: Optional[str] = Field(None, description="HeyGen voice ID (for backward compatibility)")
    is_public: bool = Field(default=False, description="Whether video is publicly shareable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="When video generation completed")
    
    class Config:
        use_enum_values = True


# Request/Response Models
class ScriptGenerationRequest(BaseModel):
    """Request to generate a script"""
    topic: str = Field(..., max_length=120, description="Topic for the script")
    target_audience: str = Field(default="general audience", description="Target audience")
    video_style: str = Field(default="professional", description="Video style")
    duration_target: int = Field(default=60, ge=15, le=300, description="Target duration in seconds")
    additional_context: Optional[str] = Field(None, description="Additional context or requirements")


class ScriptGenerationResponse(BaseModel):
    """Response from script generation"""
    script_id: int
    script: str
    topic: str
    estimated_duration: int
    quality_score: float
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class VideoGenerationRequest(BaseModel):
    """Request to generate a video"""
    script_id: Optional[int] = Field(None, description="Use existing script")
    script_text: Optional[str] = Field(None, description="Or provide script directly")
    profile_id: Optional[int] = Field(None, description="Avatar profile to use")
    avatar_id: Optional[str] = Field(None, description="Direct HeyGen avatar ID")
    voice_id: Optional[str] = Field(None, description="Direct HeyGen voice ID")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.LANDSCAPE, description="Video aspect ratio")
    background: Optional[str] = Field(None, description="Background setting")
    additional_settings: Dict[str, Any] = Field(default_factory=dict, description="Additional HeyGen settings")


class VideoGenerationResponse(BaseModel):
    """Response from video generation"""
    video_id: int
    heygen_video_id: str
    status: VideoStatus
    estimated_completion_time: Optional[int] = Field(None, description="Estimated completion in seconds")
    message: str


class VideoStatusResponse(BaseModel):
    """Video generation status response"""
    video_id: int
    heygen_video_id: str
    status: VideoStatus
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AvatarListResponse(BaseModel):
    """Response with list of available avatars"""
    avatars: List[AvatarProfile]
    total_count: int
    default_avatar_id: Optional[int] = None


class UserVideoLimits(BaseModel):
    """User video generation limits"""
    subscription_tier: SubscriptionTier
    monthly_limit: int
    videos_this_month: int
    remaining_videos: int
    credits_reset_at: Optional[datetime] = None
    is_admin: bool = False


class VideoAnalytics(BaseModel):
    """Video performance analytics"""
    video_id: int
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    engagement_rate: float = 0.0
    watch_time_avg: Optional[float] = None
    completion_rate: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
