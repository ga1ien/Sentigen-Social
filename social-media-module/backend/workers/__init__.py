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

from workers.research_worker import ResearchWorker
from workers.content_worker import ContentWorker
from workers.tool_worker import ToolWorker
from workers.image_worker import ImageWorker
from workers.midjourney_worker import MidjourneyWorker
from workers.avatar_video_worker import AvatarVideoWorker
from workers.video_worker import VideoWorker

__all__ = [
    "ResearchWorker",
    "ContentWorker", 
    "ToolWorker",
    "ImageWorker",
    "MidjourneyWorker",
    "AvatarVideoWorker",
    "VideoWorker"
]