"""
Content Intelligence Orchestrator
Manages multiple Chrome MCP workers for parallel social media scanning
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import structlog
from pydantic_ai import Agent

from workers.chrome_mcp_worker import ChromeMCPWorker, Platform, ContentInsight, PLATFORM_CONFIGS
from workers.base_worker import WorkerTask
from database.supabase_client import SupabaseClient

logger = structlog.get_logger(__name__)


class ContentIntelligenceOrchestrator:
    """Orchestrates multiple Chrome MCP workers for parallel data collection"""
    
    def __init__(self, num_workers: int = 3, db_client: Optional[SupabaseClient] = None):
        self.num_workers = num_workers
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.db_client = db_client or SupabaseClient()
        self.workers = [ChromeMCPWorker() for _ in range(num_workers)]
        self.insights_cache = []
        self.recommendations_agent = self._create_recommendations_agent()
        
        logger.info("Content Intelligence Orchestrator initialized", 
                   num_workers=num_workers)
    
    def _create_recommendations_agent(self) -> Agent:
        """Create AI agent for generating content recommendations"""
        return Agent(
            model="claude-3-5-sonnet-20241022",
            system_prompt="""
            You are an expert content strategist and social media analyst.
            
            Analyze social media insights and generate actionable content recommendations.
            
            Focus on:
            1. High-engagement topics and trends
            2. Content gaps in the market
            3. Emerging trends before they peak
            4. Optimal content formats for each platform
            5. Best posting strategies and timing
            6. Audience interests and pain points
            7. Viral content patterns
            
            Generate specific, actionable recommendations that include:
            - Compelling content titles
            - Target platforms
            - Content format (article, video, infographic, etc.)
            - Key talking points
            - Hashtag suggestions
            - Estimated engagement potential
            - Best posting times
            
            Base recommendations on data-driven insights from the provided social media analysis.
            """,
            retries=2
        )
    
    async def scan_platforms(
        self,
        platforms: List[Platform],
        search_queries: Optional[List[str]] = None,
        time_window: timedelta = timedelta(days=1),
        max_posts_per_platform: int = 20
    ) -> Dict[str, Any]:
        """
        Scan multiple platforms in parallel using Chrome MCP workers
        """
        start_time = datetime.utcnow()
        
        logger.info("Starting platform scan", 
                   platforms=[p.value for p in platforms],
                   search_queries=search_queries)
        
        # Create tasks for each platform
        tasks = []
        for i, platform in enumerate(platforms):
            config = PLATFORM_CONFIGS.get(platform)
            if config:
                worker = self.workers[i % len(self.workers)]
                task = self._create_platform_task(
                    worker,
                    platform, 
                    config,
                    search_queries,
                    time_window,
                    max_posts_per_platform
                )
                tasks.append(task)
        
        # Execute tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process and aggregate results
        aggregated_insights = self._aggregate_insights(results)
        
        # Store insights in database
        await self._store_insights(aggregated_insights)
        
        # Generate content recommendations
        recommendations = await self._generate_content_recommendations(
            aggregated_insights
        )
        
        # Store recommendations
        await self._store_recommendations(recommendations)
        
        # Analyze trends and patterns
        trending_topics = self._extract_trending_topics(aggregated_insights)
        engagement_analysis = self._analyze_engagement_patterns(aggregated_insights)
        
        scan_duration = (datetime.utcnow() - start_time).total_seconds()
        
        result = {
            "scan_id": self._generate_scan_id(),
            "scan_timestamp": start_time.isoformat(),
            "scan_duration_seconds": scan_duration,
            "platforms_scanned": [p.value for p in platforms],
            "total_insights": len(aggregated_insights),
            "insights": [insight.to_dict() for insight in aggregated_insights],
            "content_recommendations": recommendations,
            "trending_topics": trending_topics,
            "engagement_analysis": engagement_analysis,
            "search_queries": search_queries or [],
            "success_rate": self._calculate_success_rate(results)
        }
        
        # Store scan history
        await self._store_scan_history(result)
        
        logger.info("Platform scan completed", 
                   total_insights=len(aggregated_insights),
                   duration=scan_duration)
        
        return result
    
    async def _create_platform_task(
        self,
        worker: ChromeMCPWorker,
        platform: Platform,
        config,
        search_queries: Optional[List[str]],
        time_window: timedelta,
        max_posts: int
    ):
        """Create a task for scanning a specific platform"""
        
        task_data = {
            "platform": platform.value,
            "search_query": search_queries[0] if search_queries else None,
            "date_filter": (datetime.utcnow() - time_window).isoformat(),
            "max_posts": max_posts
        }
        
        task = WorkerTask(
            id=f"scan_{platform.value}_{datetime.utcnow().timestamp()}",
            type="social_intelligence",
            data=task_data
        )
        
        try:
            result = await worker.process_task(task)
            
            return {
                "platform": platform,
                "success": result.status == "completed",
                "insights": self._parse_insights_from_result(result, platform),
                "errors": [result.error] if result.error else [],
                "metadata": result.metadata
            }
        except Exception as e:
            logger.error("Platform task failed", platform=platform.value, error=str(e))
            return {
                "platform": platform,
                "success": False,
                "insights": [],
                "errors": [str(e)],
                "metadata": {}
            }
    
    def _parse_insights_from_result(
        self, 
        result, 
        platform: Platform
    ) -> List[ContentInsight]:
        """Parse insights from worker result"""
        insights = []
        
        try:
            if result.result and "insights" in result.result:
                for insight_data in result.result["insights"]:
                    insight = ContentInsight(
                        platform=platform,
                        url=insight_data.get("url", ""),
                        title=insight_data.get("title", ""),
                        content=insight_data.get("content", ""),
                        engagement_score=insight_data.get("engagement_score", 0),
                        trending_topics=insight_data.get("trending_topics", []),
                        sentiment=insight_data.get("sentiment", "neutral"),
                        author=insight_data.get("author"),
                        comments_summary=insight_data.get("comments_summary"),
                        metadata=insight_data.get("metadata", {})
                    )
                    insights.append(insight)
        except Exception as e:
            logger.error("Failed to parse insights", error=str(e))
        
        return insights
    
    def _aggregate_insights(
        self, 
        results: List[Dict[str, Any]]
    ) -> List[ContentInsight]:
        """Aggregate insights from all platforms"""
        all_insights = []
        
        for result in results:
            if result and not isinstance(result, Exception):
                if result.get("success"):
                    all_insights.extend(result.get("insights", []))
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_insights = []
        
        for insight in all_insights:
            if insight.url not in seen_urls:
                seen_urls.add(insight.url)
                unique_insights.append(insight)
        
        # Sort by engagement score
        unique_insights.sort(key=lambda x: x.engagement_score, reverse=True)
        
        return unique_insights
    
    def _extract_trending_topics(
        self, 
        insights: List[ContentInsight]
    ) -> Dict[str, int]:
        """Extract trending topics across all platforms"""
        topic_counts = defaultdict(int)
        
        for insight in insights:
            for topic in insight.trending_topics:
                topic_counts[topic.lower()] += 1
        
        # Sort by frequency and return top 20
        sorted_topics = dict(
            sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        )
        
        return sorted_topics
    
    def _analyze_engagement_patterns(
        self, 
        insights: List[ContentInsight]
    ) -> Dict[str, Any]:
        """Analyze engagement patterns across platforms"""
        
        if not insights:
            return {}
        
        try:
            df = pd.DataFrame([i.to_dict() for i in insights])
            
            analysis = {
                "avg_engagement_by_platform": df.groupby('platform')['engagement_score'].mean().to_dict(),
                "top_performing_content": df.nlargest(5, 'engagement_score')[
                    ['title', 'platform', 'engagement_score', 'url']
                ].to_dict('records'),
                "sentiment_distribution": df['sentiment'].value_counts().to_dict(),
                "content_length_analysis": self._analyze_content_length(df),
                "platform_distribution": df['platform'].value_counts().to_dict(),
                "author_analysis": self._analyze_top_authors(df)
            }
            
            return analysis
        except Exception as e:
            logger.error("Failed to analyze engagement patterns", error=str(e))
            return {}
    
    def _analyze_content_length(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze content length vs engagement"""
        try:
            df['content_length'] = df['content'].str.len()
            
            # Bin content into length categories
            bins = [0, 100, 300, 500, 1000, 5000]
            labels = ['very_short', 'short', 'medium', 'long', 'very_long']
            df['length_category'] = pd.cut(df['content_length'], bins=bins, labels=labels)
            
            return {
                "avg_engagement_by_length": df.groupby('length_category')['engagement_score'].mean().to_dict(),
                "content_count_by_length": df['length_category'].value_counts().to_dict()
            }
        except Exception as e:
            logger.error("Content length analysis failed", error=str(e))
            return {}
    
    def _analyze_top_authors(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze top performing authors"""
        try:
            author_stats = df[df['author'].notna()].groupby('author').agg({
                'engagement_score': ['mean', 'count', 'sum']
            }).round(2)
            
            author_stats.columns = ['avg_engagement', 'post_count', 'total_engagement']
            top_authors = author_stats.nlargest(10, 'total_engagement').to_dict('index')
            
            return {
                "top_authors_by_total_engagement": top_authors,
                "total_unique_authors": len(author_stats)
            }
        except Exception as e:
            logger.error("Author analysis failed", error=str(e))
            return {}
    
    async def _generate_content_recommendations(
        self, 
        insights: List[ContentInsight]
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered content recommendations based on insights"""
        
        if not insights:
            return []
        
        try:
            # Prepare insights summary for AI analysis
            insights_summary = self._summarize_insights_for_ai(insights[:30])  # Top 30
            
            prompt = f"""
            Based on the following social media insights, generate 8 specific content recommendations:
            
            {insights_summary}
            
            For each recommendation, provide:
            1. Compelling title
            2. Brief description (2-3 sentences)
            3. Target platforms (array)
            4. Content type (article, video, infographic, thread, etc.)
            5. Key talking points (3-5 points)
            6. Suggested hashtags (5-8 hashtags)
            7. Estimated engagement level (high/medium/low)
            8. Best posting time/day
            9. Target audience
            10. Content angle/hook
            
            Focus on trending topics, high-engagement patterns, and content gaps.
            Make recommendations actionable and specific.
            
            Return as a JSON array of recommendation objects.
            """
            
            result = await self.recommendations_agent.run(prompt)
            
            # Parse AI response
            recommendations = self._parse_ai_recommendations(result.output)
            
            logger.info("Generated content recommendations", count=len(recommendations))
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to generate recommendations", error=str(e))
            return self._get_fallback_recommendations(insights)
    
    def _summarize_insights_for_ai(self, insights: List[ContentInsight]) -> str:
        """Create a summary of insights for AI analysis"""
        summary = {
            "total_insights": len(insights),
            "platforms": list(set(i.platform.value for i in insights)),
            "top_content": [],
            "trending_topics": {},
            "sentiment_breakdown": {"positive": 0, "negative": 0, "neutral": 0}
        }
        
        # Top performing content
        for insight in insights[:10]:
            summary["top_content"].append({
                "platform": insight.platform.value,
                "title": insight.title,
                "engagement": insight.engagement_score,
                "topics": insight.trending_topics[:3],
                "sentiment": insight.sentiment
            })
        
        # Trending topics
        topic_counts = defaultdict(int)
        for insight in insights:
            for topic in insight.trending_topics:
                topic_counts[topic] += 1
            summary["sentiment_breakdown"][insight.sentiment] += 1
        
        summary["trending_topics"] = dict(
            sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        )
        
        return json.dumps(summary, indent=2)
    
    def _parse_ai_recommendations(self, ai_output: str) -> List[Dict[str, Any]]:
        """Parse AI recommendations from output"""
        try:
            # Try to extract JSON from the output
            import re
            json_match = re.search(r'\[.*\]', ai_output, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations
        except Exception as e:
            logger.error("Failed to parse AI recommendations", error=str(e))
        
        # Fallback to manual parsing or default recommendations
        return self._get_default_recommendations()
    
    def _get_fallback_recommendations(self, insights: List[ContentInsight]) -> List[Dict[str, Any]]:
        """Generate fallback recommendations based on insights"""
        recommendations = []
        
        # Extract top topics
        topic_counts = defaultdict(int)
        for insight in insights:
            for topic in insight.trending_topics:
                topic_counts[topic] += 1
        
        top_topics = list(dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]).keys())
        
        # Generate recommendations for top topics
        for i, topic in enumerate(top_topics):
            recommendations.append({
                "title": f"The Ultimate Guide to {topic} in 2024",
                "description": f"Comprehensive guide covering the latest trends and best practices in {topic}.",
                "platforms": ["linkedin", "twitter", "medium"],
                "content_type": "article",
                "estimated_engagement": "high" if i < 2 else "medium",
                "keywords": [topic, "guide", "2024", "trends"],
                "target_audience": "professionals and enthusiasts",
                "content_angle": "educational and actionable"
            })
        
        return recommendations
    
    def _get_default_recommendations(self) -> List[Dict[str, Any]]:
        """Get default content recommendations"""
        return [
            {
                "title": "AI Tools That Will Transform Your Workflow in 2024",
                "description": "Discover cutting-edge AI tools that can automate tasks and boost productivity.",
                "platforms": ["linkedin", "twitter"],
                "content_type": "article",
                "estimated_engagement": "high",
                "keywords": ["AI", "productivity", "automation", "tools"],
                "target_audience": "professionals and entrepreneurs",
                "content_angle": "practical and actionable"
            }
        ]
    
    async def _store_insights(self, insights: List[ContentInsight]):
        """Store insights in database"""
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
                    "comments_summary": insight.comments_summary,
                    "extracted_at": insight.extracted_at.isoformat(),
                    "metadata": insight.metadata
                }).execute()
        except Exception as e:
            logger.error("Failed to store insights", error=str(e))
    
    async def _store_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Store recommendations in database"""
        try:
            for rec in recommendations:
                await self.db_client.service_client.table("content_recommendations").insert({
                    "title": rec.get("title", ""),
                    "description": rec.get("description", ""),
                    "platforms": rec.get("platforms", []),
                    "estimated_engagement": rec.get("estimated_engagement", "medium"),
                    "content_type": rec.get("content_type", "article"),
                    "keywords": rec.get("keywords", []),
                    "target_audience": rec.get("target_audience", ""),
                    "content_angle": rec.get("content_angle", "")
                }).execute()
        except Exception as e:
            logger.error("Failed to store recommendations", error=str(e))
    
    async def _store_scan_history(self, scan_result: Dict[str, Any]):
        """Store scan history in database"""
        try:
            await self.db_client.service_client.table("scan_history").insert({
                "scan_id": scan_result["scan_id"],
                "platforms": scan_result["platforms_scanned"],
                "search_queries": scan_result["search_queries"],
                "insights_count": scan_result["total_insights"],
                "trending_topics": scan_result["trending_topics"],
                "engagement_analysis": scan_result["engagement_analysis"],
                "scan_duration_seconds": scan_result["scan_duration_seconds"],
                "success_rate": scan_result["success_rate"]
            }).execute()
        except Exception as e:
            logger.error("Failed to store scan history", error=str(e))
    
    def _calculate_success_rate(self, results: List[Dict[str, Any]]) -> float:
        """Calculate success rate of platform scans"""
        if not results:
            return 0.0
        
        successful = sum(1 for r in results if r and not isinstance(r, Exception) and r.get("success"))
        return round(successful / len(results), 2)
    
    def _generate_scan_id(self) -> str:
        """Generate unique scan ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def get_recent_insights(
        self, 
        platform: Optional[str] = None, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent insights from database"""
        try:
            query = self.db_client.service_client.table("content_insights").select("*")
            
            if platform:
                query = query.eq("platform", platform)
            
            result = query.order("extracted_at", desc=True).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            logger.error("Failed to get recent insights", error=str(e))
            return []
    
    async def get_recent_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent recommendations from database"""
        try:
            result = self.db_client.service_client.table("content_recommendations").select("*").order("generated_at", desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error("Failed to get recent recommendations", error=str(e))
            return []
    
    async def close(self):
        """Close orchestrator and cleanup resources"""
        for worker in self.workers:
            await worker.close()
        
        if self.db_client:
            await self.db_client.close()
        
        logger.info("Content Intelligence Orchestrator closed")
