"""
Content Intelligence API Routes
Endpoints for Chrome MCP-powered social media intelligence
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field

from services.content_intelligence_orchestrator import ContentIntelligenceOrchestrator
from workers.chrome_mcp_worker import Platform
from database.supabase_client import SupabaseClient
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/content-intelligence", tags=["content-intelligence"])

# Global orchestrator instance
orchestrator = None

async def get_orchestrator() -> ContentIntelligenceOrchestrator:
    """Get or create orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = ContentIntelligenceOrchestrator(num_workers=3)
    return orchestrator


# Request/Response Models
class ScanRequest(BaseModel):
    """Request model for platform scanning"""
    platforms: List[str] = Field(..., description="List of platforms to scan")
    search_queries: Optional[List[str]] = Field(default=None, description="Search queries to use")
    time_window_hours: int = Field(default=24, description="Time window in hours")
    max_posts_per_platform: int = Field(default=20, description="Maximum posts per platform")


class ScheduledScanConfig(BaseModel):
    """Configuration for scheduled scans"""
    platforms: List[str] = Field(..., description="Platforms to scan")
    interval_hours: int = Field(default=6, description="Scan interval in hours")
    search_queries: Optional[List[str]] = Field(default=None, description="Search queries")
    max_posts_per_platform: int = Field(default=20, description="Max posts per platform")


class ScanResponse(BaseModel):
    """Response model for scan operations"""
    status: str
    scan_id: str
    message: str
    results: Optional[Dict[str, Any]] = None


class InsightResponse(BaseModel):
    """Response model for insights"""
    insights: List[Dict[str, Any]]
    total_count: int
    generated_at: str
    platform_filter: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    recommendations: List[Dict[str, Any]]
    generated_at: str
    total_count: int


# Store for scheduled scans
scheduled_scans: Dict[str, Dict[str, Any]] = {}


@router.post("/scan", response_model=ScanResponse)
async def scan_platforms(
    request: ScanRequest,
    orchestrator: ContentIntelligenceOrchestrator = Depends(get_orchestrator)
):
    """
    Trigger a scan of specified platforms for content insights
    
    This endpoint uses Chrome MCP to scan social media platforms and extract
    high-engagement content, trending topics, and actionable insights.
    """
    try:
        # Validate platforms
        valid_platforms = []
        for platform_str in request.platforms:
            try:
                platform = Platform(platform_str.lower())
                valid_platforms.append(platform)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported platform: {platform_str}"
                )
        
        if not valid_platforms:
            raise HTTPException(
                status_code=400,
                detail="At least one valid platform is required"
            )
        
        logger.info("Starting platform scan", 
                   platforms=[p.value for p in valid_platforms],
                   search_queries=request.search_queries)
        
        # Execute the scan
        results = await orchestrator.scan_platforms(
            platforms=valid_platforms,
            search_queries=request.search_queries,
            time_window=timedelta(hours=request.time_window_hours),
            max_posts_per_platform=request.max_posts_per_platform
        )
        
        return ScanResponse(
            status="success",
            scan_id=results["scan_id"],
            message=f"Successfully scanned {len(valid_platforms)} platforms and found {results['total_insights']} insights",
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Platform scan failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/schedule-scan", response_model=ScanResponse)
async def schedule_recurring_scan(
    config: ScheduledScanConfig,
    background_tasks: BackgroundTasks,
    orchestrator: ContentIntelligenceOrchestrator = Depends(get_orchestrator)
):
    """
    Schedule recurring scans of platforms
    
    Sets up automated scanning at specified intervals to continuously
    monitor social media platforms for trending content and insights.
    """
    try:
        scan_id = str(uuid4())
        
        # Validate platforms
        valid_platforms = []
        for platform_str in config.platforms:
            try:
                platform = Platform(platform_str.lower())
                valid_platforms.append(platform)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported platform: {platform_str}"
                )
        
        scheduled_scans[scan_id] = {
            "config": config,
            "platforms": [p.value for p in valid_platforms],
            "next_run": datetime.utcnow() + timedelta(hours=config.interval_hours),
            "status": "scheduled",
            "created_at": datetime.utcnow()
        }
        
        # Add to background tasks
        background_tasks.add_task(
            run_scheduled_scan,
            scan_id,
            config,
            valid_platforms,
            orchestrator
        )
        
        logger.info("Scheduled recurring scan", 
                   scan_id=scan_id,
                   platforms=[p.value for p in valid_platforms],
                   interval_hours=config.interval_hours)
        
        return ScanResponse(
            status="scheduled",
            scan_id=scan_id,
            message=f"Scheduled recurring scan for {len(valid_platforms)} platforms every {config.interval_hours} hours",
            results={
                "next_run": scheduled_scans[scan_id]["next_run"].isoformat(),
                "interval_hours": config.interval_hours,
                "platforms": [p.value for p in valid_platforms]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to schedule scan", error=str(e))
        raise HTTPException(status_code=500, detail=f"Scheduling failed: {str(e)}")


@router.get("/scheduled-scans")
async def get_scheduled_scans():
    """Get list of all scheduled scans"""
    return {
        "scheduled_scans": [
            {
                "scan_id": scan_id,
                "platforms": scan_data["platforms"],
                "status": scan_data["status"],
                "next_run": scan_data["next_run"].isoformat(),
                "created_at": scan_data["created_at"].isoformat()
            }
            for scan_id, scan_data in scheduled_scans.items()
        ],
        "total_count": len(scheduled_scans)
    }


@router.delete("/scheduled-scans/{scan_id}")
async def cancel_scheduled_scan(scan_id: str):
    """Cancel a scheduled scan"""
    if scan_id not in scheduled_scans:
        raise HTTPException(status_code=404, detail="Scheduled scan not found")
    
    del scheduled_scans[scan_id]
    
    return {
        "status": "cancelled",
        "scan_id": scan_id,
        "message": "Scheduled scan cancelled successfully"
    }


@router.get("/insights/trending", response_model=InsightResponse)
async def get_trending_insights(
    platform: Optional[str] = None,
    limit: int = 20,
    orchestrator: ContentIntelligenceOrchestrator = Depends(get_orchestrator)
):
    """
    Get trending content insights
    
    Returns the most engaging and trending content from recent scans,
    optionally filtered by platform.
    """
    try:
        # Validate platform if provided
        if platform:
            try:
                Platform(platform.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported platform: {platform}"
                )
        
        insights = await orchestrator.get_recent_insights(
            platform=platform.lower() if platform else None,
            limit=limit
        )
        
        return InsightResponse(
            insights=insights,
            total_count=len(insights),
            generated_at=datetime.utcnow().isoformat(),
            platform_filter=platform
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get trending insights", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_content_recommendations(
    regenerate: bool = False,
    limit: int = 10,
    orchestrator: ContentIntelligenceOrchestrator = Depends(get_orchestrator)
):
    """
    Get AI-generated content recommendations
    
    Returns content recommendations based on recent social media insights.
    Set regenerate=true to create fresh recommendations.
    """
    try:
        if regenerate:
            # Get recent insights and generate new recommendations
            recent_insights_data = await orchestrator.get_recent_insights(limit=50)
            
            # Convert to ContentInsight objects
            from workers.chrome_mcp_worker import ContentInsight
            insights = []
            for data in recent_insights_data:
                try:
                    insight = ContentInsight(
                        platform=Platform(data["platform"]),
                        url=data["url"],
                        title=data["title"],
                        content=data["content"],
                        engagement_score=data["engagement_score"],
                        trending_topics=data.get("trending_topics", []),
                        sentiment=data.get("sentiment", "neutral"),
                        author=data.get("author"),
                        comments_summary=data.get("comments_summary"),
                        extracted_at=datetime.fromisoformat(data["extracted_at"].replace('Z', '+00:00')),
                        metadata=data.get("metadata", {})
                    )
                    insights.append(insight)
                except Exception as e:
                    logger.warning("Failed to parse insight", error=str(e))
                    continue
            
            recommendations = await orchestrator._generate_content_recommendations(insights)
            await orchestrator._store_recommendations(recommendations)
        else:
            recommendations = await orchestrator.get_recent_recommendations(limit=limit)
        
        return RecommendationResponse(
            recommendations=recommendations,
            generated_at=datetime.utcnow().isoformat(),
            total_count=len(recommendations)
        )
        
    except Exception as e:
        logger.error("Failed to get recommendations", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/analytics/trending-topics")
async def get_trending_topics(
    time_window_hours: int = 24,
    limit: int = 20
):
    """Get trending topics from recent insights"""
    try:
        db_client = SupabaseClient()
        
        # Get insights from the specified time window
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        result = db_client.service_client.table("content_insights").select("trending_topics").gte("extracted_at", cutoff_time.isoformat()).execute()
        
        # Count topic frequencies
        topic_counts = {}
        for row in result.data:
            topics = row.get("trending_topics", [])
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort and limit
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return {
            "trending_topics": [
                {"topic": topic, "count": count, "trend_score": count * 10}
                for topic, count in sorted_topics
            ],
            "time_window_hours": time_window_hours,
            "total_topics": len(topic_counts),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get trending topics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get trending topics: {str(e)}")


@router.get("/analytics/engagement-patterns")
async def get_engagement_patterns(
    time_window_hours: int = 168,  # 1 week
    platform: Optional[str] = None
):
    """Get engagement pattern analysis"""
    try:
        db_client = SupabaseClient()
        
        # Build query
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        query = db_client.service_client.table("content_insights").select("*").gte("extracted_at", cutoff_time.isoformat())
        
        if platform:
            query = query.eq("platform", platform.lower())
        
        result = query.execute()
        
        if not result.data:
            return {
                "message": "No data available for analysis",
                "time_window_hours": time_window_hours,
                "platform_filter": platform
            }
        
        # Analyze patterns
        import pandas as pd
        df = pd.DataFrame(result.data)
        
        analysis = {
            "avg_engagement_by_platform": df.groupby('platform')['engagement_score'].mean().to_dict(),
            "sentiment_distribution": df['sentiment'].value_counts().to_dict(),
            "top_performing_content": df.nlargest(5, 'engagement_score')[
                ['title', 'platform', 'engagement_score', 'url']
            ].to_dict('records'),
            "platform_distribution": df['platform'].value_counts().to_dict(),
            "time_window_hours": time_window_hours,
            "total_insights_analyzed": len(df),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        logger.error("Failed to get engagement patterns", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get engagement patterns: {str(e)}")


@router.get("/health")
async def health_check(
    orchestrator: ContentIntelligenceOrchestrator = Depends(get_orchestrator)
):
    """Health check for content intelligence service"""
    try:
        # Check Chrome MCP connection
        chrome_mcp_healthy = False
        if orchestrator.workers:
            chrome_mcp_healthy = await orchestrator.workers[0].health_check()
        
        # Check database connection
        db_healthy = await orchestrator.db_client.health_check()
        
        return {
            "status": "healthy" if chrome_mcp_healthy and db_healthy else "degraded",
            "chrome_mcp_connected": chrome_mcp_healthy,
            "database_connected": db_healthy,
            "active_workers": len(orchestrator.workers),
            "scheduled_scans": len(scheduled_scans),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Background task for scheduled scans
async def run_scheduled_scan(
    scan_id: str,
    config: ScheduledScanConfig,
    platforms: List[Platform],
    orchestrator: ContentIntelligenceOrchestrator
):
    """Background task to run scheduled scans"""
    logger.info("Starting scheduled scan background task", scan_id=scan_id)
    
    while scan_id in scheduled_scans:
        try:
            # Wait until next run time
            next_run = scheduled_scans[scan_id]["next_run"]
            wait_seconds = (next_run - datetime.utcnow()).total_seconds()
            
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            
            # Check if scan was cancelled
            if scan_id not in scheduled_scans:
                break
            
            logger.info("Executing scheduled scan", scan_id=scan_id)
            
            # Update status
            scheduled_scans[scan_id]["status"] = "running"
            
            # Run the scan
            results = await orchestrator.scan_platforms(
                platforms=platforms,
                search_queries=config.search_queries,
                time_window=timedelta(hours=config.interval_hours),
                max_posts_per_platform=config.max_posts_per_platform
            )
            
            # Update scan record
            scheduled_scans[scan_id].update({
                "status": "scheduled",
                "last_run": datetime.utcnow(),
                "next_run": datetime.utcnow() + timedelta(hours=config.interval_hours),
                "last_result": {
                    "insights_count": results["total_insights"],
                    "success_rate": results["success_rate"]
                }
            })
            
            logger.info("Scheduled scan completed", 
                       scan_id=scan_id,
                       insights_count=results["total_insights"])
            
        except Exception as e:
            logger.error("Scheduled scan failed", scan_id=scan_id, error=str(e))
            
            # Update error status
            if scan_id in scheduled_scans:
                scheduled_scans[scan_id].update({
                    "status": "error",
                    "last_error": str(e),
                    "error_time": datetime.utcnow(),
                    "next_run": datetime.utcnow() + timedelta(hours=config.interval_hours)
                })
            
            # Wait before retrying
            await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    logger.info("Scheduled scan background task ended", scan_id=scan_id)
