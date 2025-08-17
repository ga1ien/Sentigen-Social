"""
Research-to-Video Workflow Orchestrator

Complete workflow:
1. Chrome MCP Server → Research & data collection
2. Supabase → Store research reports and insights  
3. AI Script Generation → Create video scripts from research
4. HeyGen → Generate AI videos from scripts
5. User Approval → Review before posting
6. TikTok Publishing → Post approved videos
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import structlog

from workers.chrome_mcp_worker import ChromeMCPWorker, Platform, ContentInsight
from workers.avatar_video_worker import AvatarVideoWorker
from workers.content_worker import ContentWorker
from database.supabase_client import SupabaseClient
from utils.ayrshare_client import AyrshareClient
from utils.model_config import get_smart_model

logger = structlog.get_logger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    SCRIPT_GENERATION = "script_generation"
    VIDEO_GENERATION = "video_generation"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowConfig:
    """Configuration for research-to-video workflow"""
    research_topics: List[str]
    platforms_to_research: List[Platform]
    target_audience: str
    video_style: str = "professional"  # professional, casual, educational
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    max_video_duration: int = 60  # seconds
    auto_publish: bool = False  # if True, skips approval step
    tiktok_hashtags: List[str] = None
    

@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    workflow_id: str
    status: WorkflowStatus
    research_insights: List[ContentInsight]
    generated_script: Optional[str]
    video_url: Optional[str]
    video_metadata: Optional[Dict[str, Any]]
    approval_status: Optional[str]
    published_post_ids: List[str]
    error_message: Optional[str]
    execution_time: float
    created_at: datetime
    completed_at: Optional[datetime]


class ResearchToVideoWorkflow:
    """Orchestrates the complete research-to-video workflow"""
    
    def __init__(self):
        """Initialize workflow orchestrator"""
        self.db_client = SupabaseClient()
        self.chrome_worker = ChromeMCPWorker()
        self.content_worker = ContentWorker()
        self.video_worker = AvatarVideoWorker()
        self.ayrshare_client = AyrshareClient()
        
        logger.info("Research-to-Video Workflow initialized")
    
    async def execute_workflow(
        self, 
        config: WorkflowConfig,
        user_id: str,
        workspace_id: str
    ) -> WorkflowResult:
        """Execute the complete research-to-video workflow"""
        
        workflow_id = f"rtv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        
        logger.info("Starting research-to-video workflow", 
                   workflow_id=workflow_id, config=config)
        
        try:
            # Store workflow execution record
            await self._store_workflow_execution(
                workflow_id, config, user_id, workspace_id, WorkflowStatus.PENDING
            )
            
            # Step 1: Research Phase
            await self._update_workflow_status(workflow_id, WorkflowStatus.RESEARCHING)
            research_insights = await self._execute_research_phase(config, workflow_id)
            
            if not research_insights:
                raise Exception("No research insights found")
            
            # Step 2: Analysis & Script Generation
            await self._update_workflow_status(workflow_id, WorkflowStatus.SCRIPT_GENERATION)
            script = await self._generate_video_script(research_insights, config)
            
            if not script:
                raise Exception("Failed to generate video script")
            
            # Step 3: Video Generation
            await self._update_workflow_status(workflow_id, WorkflowStatus.VIDEO_GENERATION)
            video_result = await self._generate_video(script, config)
            
            if not video_result or not video_result.get("video_url"):
                raise Exception("Failed to generate video")
            
            # Step 4: User Approval (if required)
            if not config.auto_publish:
                await self._update_workflow_status(workflow_id, WorkflowStatus.AWAITING_APPROVAL)
                # Store for manual approval - workflow pauses here
                await self._store_pending_approval(
                    workflow_id, script, video_result, config
                )
                
                # Return result with awaiting approval status
                return WorkflowResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.AWAITING_APPROVAL,
                    research_insights=research_insights,
                    generated_script=script,
                    video_url=video_result.get("video_url"),
                    video_metadata=video_result,
                    approval_status="pending",
                    published_post_ids=[],
                    error_message=None,
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                    created_at=start_time,
                    completed_at=None
                )
            
            # Step 5: Auto-publish (if enabled)
            published_post_ids = await self._publish_to_tiktok(
                video_result, script, config, workflow_id
            )
            
            # Complete workflow
            await self._update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)
            completion_time = datetime.utcnow()
            
            result = WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                research_insights=research_insights,
                generated_script=script,
                video_url=video_result.get("video_url"),
                video_metadata=video_result,
                approval_status="auto_approved" if config.auto_publish else "approved",
                published_post_ids=published_post_ids,
                error_message=None,
                execution_time=(completion_time - start_time).total_seconds(),
                created_at=start_time,
                completed_at=completion_time
            )
            
            await self._store_workflow_result(result)
            return result
            
        except Exception as e:
            logger.error("Workflow execution failed", 
                        workflow_id=workflow_id, error=str(e))
            
            await self._update_workflow_status(workflow_id, WorkflowStatus.FAILED)
            
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                research_insights=[],
                generated_script=None,
                video_url=None,
                video_metadata=None,
                approval_status=None,
                published_post_ids=[],
                error_message=str(e),
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                created_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    async def _execute_research_phase(
        self, 
        config: WorkflowConfig, 
        workflow_id: str
    ) -> List[ContentInsight]:
        """Execute research phase using Chrome MCP"""
        
        all_insights = []
        
        for platform in config.platforms_to_research:
            for topic in config.research_topics:
                try:
                    logger.info("Researching platform", 
                               platform=platform.value, topic=topic)
                    
                    # Create research task
                    task_data = {
                        "platform": platform.value,
                        "search_query": topic,
                        "max_posts": 10,
                        "date_filter": "week"  # Last week's content
                    }
                    
                    # Execute Chrome MCP research
                    from workers.base_worker import WorkerTask
                    task = WorkerTask(
                        id=f"{workflow_id}_{platform.value}_{topic}",
                        task_type="research",
                        data=task_data
                    )
                    
                    result = await self.chrome_worker.process_task(task)
                    
                    if result.status == "completed" and result.result:
                        insights_data = result.result.get("insights", [])
                        
                        # Convert to ContentInsight objects
                        for insight_data in insights_data:
                            insight = ContentInsight(
                                platform=Platform(insight_data["platform"]),
                                url=insight_data["url"],
                                title=insight_data["title"],
                                content=insight_data["content"],
                                engagement_score=insight_data["engagement_score"],
                                trending_topics=insight_data["trending_topics"],
                                sentiment=insight_data["sentiment"],
                                author=insight_data.get("author"),
                                extracted_at=datetime.fromisoformat(
                                    insight_data["extracted_at"].replace("Z", "+00:00")
                                )
                            )
                            all_insights.append(insight)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error("Research failed for platform", 
                               platform=platform.value, topic=topic, error=str(e))
                    continue
        
        # Store insights in Supabase
        await self._store_research_insights(all_insights, workflow_id)
        
        # Return top insights by engagement
        all_insights.sort(key=lambda x: x.engagement_score, reverse=True)
        return all_insights[:20]  # Top 20 insights
    
    async def _generate_video_script(
        self, 
        insights: List[ContentInsight], 
        config: WorkflowConfig
    ) -> str:
        """Generate video script from research insights"""
        
        # Prepare insights summary
        insights_summary = []
        trending_topics = set()
        
        for insight in insights[:10]:  # Top 10 insights
            insights_summary.append({
                "platform": insight.platform.value,
                "title": insight.title,
                "content": insight.content[:200],  # Truncate
                "engagement_score": insight.engagement_score,
                "sentiment": insight.sentiment
            })
            trending_topics.update(insight.trending_topics)
        
        # Create script generation prompt
        prompt = f"""
        Create a compelling {config.max_video_duration}-second video script for {config.target_audience} based on these research insights:
        
        RESEARCH INSIGHTS:
        {json.dumps(insights_summary, indent=2)}
        
        TRENDING TOPICS: {', '.join(list(trending_topics)[:10])}
        
        VIDEO STYLE: {config.video_style}
        TARGET AUDIENCE: {config.target_audience}
        
        Requirements:
        - Hook viewers in the first 3 seconds
        - Present 2-3 key insights or trends
        - Include actionable takeaways
        - End with engaging call-to-action
        - Optimize for TikTok format (vertical video)
        - Keep language conversational and engaging
        - Duration: approximately {config.max_video_duration} seconds when spoken
        
        Format the script with clear sections:
        [HOOK] - Opening 3 seconds
        [MAIN CONTENT] - Key insights and trends
        [CALL TO ACTION] - Engaging ending
        
        Make it viral-worthy and shareable!
        """
        
        try:
            # Use content worker to generate script
            from workers.base_worker import WorkerTask
            task = WorkerTask(
                id=f"script_gen_{datetime.utcnow().timestamp()}",
                task_type="script_generation",
                data={
                    "content_type": "video_script",
                    "prompt": prompt,
                    "platform": "tiktok",
                    "target_audience": config.target_audience,
                    "research_data": {"insights": insights_summary}
                }
            )
            
            result = await self.content_worker.process_task(task)
            
            if result.status == "success" and result.result:
                return result.result.get("generated_content", "")
            
        except Exception as e:
            logger.error("Script generation failed", error=str(e))
        
        return ""
    
    async def _generate_video(
        self, 
        script: str, 
        config: WorkflowConfig
    ) -> Dict[str, Any]:
        """Generate video using HeyGen"""
        
        try:
            # Use avatar video worker
            from workers.base_worker import WorkerTask
            task = WorkerTask(
                id=f"video_gen_{datetime.utcnow().timestamp()}",
                task_type="avatar_video",
                data={
                    "script": script,
                    "avatar_id": config.avatar_id,
                    "voice_id": config.voice_id,
                    "video_style": config.video_style,
                    "duration": config.max_video_duration,
                    "format": "vertical",  # TikTok format
                    "background": "professional"
                }
            )
            
            result = await self.video_worker.process_task(task)
            
            if result.status == "success" and result.result:
                return result.result
            else:
                logger.error("Video generation failed", error=result.error_message)
                return {}
                
        except Exception as e:
            logger.error("Video generation failed", error=str(e))
            return {}
    
    async def _publish_to_tiktok(
        self, 
        video_result: Dict[str, Any], 
        script: str, 
        config: WorkflowConfig,
        workflow_id: str
    ) -> List[str]:
        """Publish video to TikTok via Ayrshare"""
        
        try:
            await self._update_workflow_status(workflow_id, WorkflowStatus.PUBLISHING)
            
            # Prepare TikTok post
            video_url = video_result.get("video_url")
            if not video_url:
                raise Exception("No video URL available")
            
            # Create engaging caption from script
            caption_lines = script.split('\n')
            caption = ""
            for line in caption_lines:
                if not line.startswith('[') and line.strip():
                    caption += line.strip() + " "
                if len(caption) > 100:  # TikTok caption limit consideration
                    break
            
            # Add hashtags
            hashtags = config.tiktok_hashtags or [
                "#AI", "#TechTrends", "#SocialMedia", "#Automation", "#Productivity"
            ]
            caption += " " + " ".join(hashtags)
            
            # Post to TikTok
            result = await self.ayrshare_client.post_to_social_media(
                post_content=caption,
                platforms=["tiktok"],
                media_urls=[video_url]
            )
            
            if result.get("status") == "success":
                post_ids = [
                    post.get("id") for post in result.get("postIds", [])
                    if post.get("platform") == "tiktok"
                ]
                
                logger.info("Successfully published to TikTok", 
                           workflow_id=workflow_id, post_ids=post_ids)
                
                return post_ids
            else:
                logger.error("TikTok publishing failed", result=result)
                return []
                
        except Exception as e:
            logger.error("TikTok publishing failed", error=str(e))
            return []
    
    async def approve_and_publish(
        self, 
        workflow_id: str, 
        approved: bool,
        user_feedback: Optional[str] = None
    ) -> WorkflowResult:
        """Handle user approval and publish if approved"""
        
        try:
            # Get pending approval data
            approval_data = await self._get_pending_approval(workflow_id)
            if not approval_data:
                raise Exception("No pending approval found")
            
            if approved:
                # Update status to approved
                await self._update_workflow_status(workflow_id, WorkflowStatus.APPROVED)
                
                # Publish to TikTok
                published_post_ids = await self._publish_to_tiktok(
                    approval_data["video_result"],
                    approval_data["script"],
                    WorkflowConfig(**approval_data["config"]),
                    workflow_id
                )
                
                # Complete workflow
                await self._update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)
                
                # Update result
                result = WorkflowResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.COMPLETED,
                    research_insights=[],  # Load from DB if needed
                    generated_script=approval_data["script"],
                    video_url=approval_data["video_result"].get("video_url"),
                    video_metadata=approval_data["video_result"],
                    approval_status="approved",
                    published_post_ids=published_post_ids,
                    error_message=None,
                    execution_time=0,  # Calculate from DB
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                
                await self._store_workflow_result(result)
                return result
                
            else:
                # Rejected
                await self._update_workflow_status(workflow_id, WorkflowStatus.CANCELLED)
                
                return WorkflowResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.CANCELLED,
                    research_insights=[],
                    generated_script=approval_data["script"],
                    video_url=approval_data["video_result"].get("video_url"),
                    video_metadata=approval_data["video_result"],
                    approval_status="rejected",
                    published_post_ids=[],
                    error_message=f"User rejected: {user_feedback}",
                    execution_time=0,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error("Approval handling failed", error=str(e))
            await self._update_workflow_status(workflow_id, WorkflowStatus.FAILED)
            raise
    
    # Database operations
    async def _store_workflow_execution(
        self, 
        workflow_id: str, 
        config: WorkflowConfig,
        user_id: str,
        workspace_id: str,
        status: WorkflowStatus
    ):
        """Store workflow execution record"""
        try:
            await self.db_client.service_client.table("workflow_executions").insert({
                "id": workflow_id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "workflow_name": "research_to_video",
                "workflow_config": {
                    "research_topics": config.research_topics,
                    "platforms_to_research": [p.value for p in config.platforms_to_research],
                    "target_audience": config.target_audience,
                    "video_style": config.video_style,
                    "max_video_duration": config.max_video_duration,
                    "auto_publish": config.auto_publish
                },
                "status": status.value,
                "started_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error("Failed to store workflow execution", error=str(e))
    
    async def _update_workflow_status(self, workflow_id: str, status: WorkflowStatus):
        """Update workflow status"""
        try:
            update_data = {"status": status.value}
            if status == WorkflowStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            await self.db_client.service_client.table("workflow_executions").update(
                update_data
            ).eq("id", workflow_id).execute()
        except Exception as e:
            logger.error("Failed to update workflow status", error=str(e))
    
    async def _store_research_insights(
        self, 
        insights: List[ContentInsight], 
        workflow_id: str
    ):
        """Store research insights in database"""
        try:
            for insight in insights:
                await self.db_client.service_client.table("content_insights").insert({
                    "platform": insight.platform.value,
                    "url": insight.url,
                    "title": insight.title,
                    "content": insight.content,
                    "engagement_score": insight.engagement_score,
                    "trending_topics": insight.trending_topics,
                    "sentiment": insight.sentiment,
                    "author": insight.author,
                    "extracted_at": insight.extracted_at.isoformat(),
                    "metadata": {
                        "workflow_id": workflow_id,
                        "extraction_method": "chrome_mcp"
                    }
                }).execute()
        except Exception as e:
            logger.error("Failed to store research insights", error=str(e))
    
    async def _store_pending_approval(
        self, 
        workflow_id: str, 
        script: str, 
        video_result: Dict[str, Any],
        config: WorkflowConfig
    ):
        """Store data for pending approval"""
        try:
            await self.db_client.service_client.table("workflow_approvals").insert({
                "workflow_id": workflow_id,
                "script": script,
                "video_result": video_result,
                "config": {
                    "research_topics": config.research_topics,
                    "target_audience": config.target_audience,
                    "video_style": config.video_style,
                    "tiktok_hashtags": config.tiktok_hashtags
                },
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error("Failed to store pending approval", error=str(e))
    
    async def _get_pending_approval(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get pending approval data"""
        try:
            result = await self.db_client.service_client.table("workflow_approvals").select("*").eq(
                "workflow_id", workflow_id
            ).eq("status", "pending").execute()
            
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.error("Failed to get pending approval", error=str(e))
        
        return None
    
    async def _store_workflow_result(self, result: WorkflowResult):
        """Store final workflow result"""
        try:
            await self.db_client.service_client.table("workflow_results").insert({
                "workflow_id": result.workflow_id,
                "status": result.status.value,
                "generated_script": result.generated_script,
                "video_url": result.video_url,
                "video_metadata": result.video_metadata,
                "approval_status": result.approval_status,
                "published_post_ids": result.published_post_ids,
                "error_message": result.error_message,
                "execution_time": result.execution_time,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None
            }).execute()
        except Exception as e:
            logger.error("Failed to store workflow result", error=str(e))
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status"""
        try:
            result = await self.db_client.service_client.table("workflow_executions").select("*").eq(
                "id", workflow_id
            ).execute()
            
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.error("Failed to get workflow status", error=str(e))
        
        return None
    
    async def list_pending_approvals(self, user_id: str) -> List[Dict[str, Any]]:
        """List workflows awaiting approval for a user"""
        try:
            result = await self.db_client.service_client.table("workflow_executions").select(
                "*, workflow_approvals(*)"
            ).eq("user_id", user_id).eq("status", "awaiting_approval").execute()
            
            return result.data or []
        except Exception as e:
            logger.error("Failed to list pending approvals", error=str(e))
            return []
