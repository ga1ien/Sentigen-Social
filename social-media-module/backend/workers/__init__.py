"""
Multi-Worker System for Social Media Module

Specialized workers for different AI tasks:
- Research Worker (Perplexity)
- Content Worker (Claude 4 Sonnet) 
- Tool Worker (GPT-5 Mini)
- Image Worker (GPT-4o)
- Midjourney Worker (CometAPI - Images & Videos)
- Avatar Video Worker (HeyGen)
- Video Worker (Google Veo3)
"""

from .research_worker import ResearchWorker
from .content_worker import ContentWorker
from .tool_worker import ToolWorker
from .image_worker import ImageWorker
from .midjourney_worker import MidjourneyWorker
from .avatar_video_worker import AvatarVideoWorker
from .video_worker import VideoWorker

__all__ = [
    "ResearchWorker",
    "ContentWorker", 
    "ToolWorker",
    "ImageWorker",
    "MidjourneyWorker",
    "AvatarVideoWorker",
    "VideoWorker"
]