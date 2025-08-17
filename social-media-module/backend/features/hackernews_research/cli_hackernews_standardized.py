#!/usr/bin/env python3
"""
Standardized Hacker News Research Tool
Compliant with Project Server Standards v1.0

Features:
- Pydantic AI v0.3.2+ agent framework
- Snake_case naming conventions
- Async/await patterns
- Supabase with asyncpg
- Structured logging
- Environment variable management
"""

import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import structlog

from features.STANDARDIZED_TOOL_TEMPLATE import (
    AnalysisDepth,
    DataSource,
    ResearchConfig,
    ResearchResult,
    StandardizedResearchTool,
    run_standardized_cli,
)

logger = structlog.get_logger(__name__)


class HackerNewsAPI:
    """Hacker News API client"""

    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Standardized-HackerNews-Research-Tool/1.0"})

    def get_top_stories(self, limit: int = 30) -> List[int]:
        """Get top story IDs"""
        try:
            response = self.session.get(f"{self.base_url}/topstories.json", timeout=30)
            if response.status_code == 200:
                story_ids = response.json()
                return story_ids[:limit]
            return []
        except Exception as e:
            logger.error("Failed to get top stories", error=str(e))
            return []

    def get_new_stories(self, limit: int = 30) -> List[int]:
        """Get new story IDs"""
        try:
            response = self.session.get(f"{self.base_url}/newstories.json", timeout=30)
            if response.status_code == 200:
                story_ids = response.json()
                return story_ids[:limit]
            return []
        except Exception as e:
            logger.error("Failed to get new stories", error=str(e))
            return []

    def get_ask_stories(self, limit: int = 30) -> List[int]:
        """Get Ask HN story IDs"""
        try:
            response = self.session.get(f"{self.base_url}/askstories.json", timeout=30)
            if response.status_code == 200:
                story_ids = response.json()
                return story_ids[:limit]
            return []
        except Exception as e:
            logger.error("Failed to get Ask HN stories", error=str(e))
            return []

    def get_item(self, item_id: int) -> Optional[Dict]:
        """Get item details by ID"""
        try:
            response = self.session.get(f"{self.base_url}/item/{item_id}.json", timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error("Failed to get item", error=str(e), item_id=item_id)
            return None

    def get_story_with_comments(self, story_id: int, max_comments: int = 10) -> Optional[Dict]:
        """Get story with its top comments"""
        try:
            story = self.get_item(story_id)
            if not story:
                return None

            # Get top comments
            comments = []
            if story.get("kids") and max_comments > 0:
                comment_ids = story["kids"][:max_comments]

                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_id = {executor.submit(self.get_item, cid): cid for cid in comment_ids}

                    for future in as_completed(future_to_id):
                        comment = future.result()
                        if comment and comment.get("text"):
                            comments.append(comment)

            story["comments"] = comments
            return story

        except Exception as e:
            logger.error("Failed to get story with comments", error=str(e), story_id=story_id)
            return None


class HackerNewsResearchTool(StandardizedResearchTool):
    """Standardized Hacker News research tool implementation"""

    def __init__(self):
        super().__init__(DataSource.HACKERNEWS)
        self.hn_api = None
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the Hacker News research tool"""
        await super().initialize()

        try:
            logger.info("Initializing Hacker News research tool")

            # Initialize Hacker News API client
            self.hn_api = HackerNewsAPI()

            logger.info("Hacker News research tool initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Hacker News research tool", error=str(e))
            raise

    async def collect_raw_data(self, config: ResearchConfig) -> Dict[str, Any]:
        """Collect raw data from Hacker News"""
        try:
            logger.info("Starting Hacker News data collection", query=config.query)

            # Parse collection parameters
            story_types = config.custom_parameters.get("story_types", ["top", "new", "ask"])
            max_stories_per_type = config.max_items // len(story_types) if len(story_types) > 0 else config.max_items
            max_comments_per_story = config.custom_parameters.get("max_comments_per_story", 5)

            all_stories = []

            # Collect different types of stories
            for story_type in story_types:
                logger.info("Collecting stories", story_type=story_type)

                # Get story IDs based on type
                if story_type == "top":
                    story_ids = self.hn_api.get_top_stories(max_stories_per_type)
                elif story_type == "new":
                    story_ids = self.hn_api.get_new_stories(max_stories_per_type)
                elif story_type == "ask":
                    story_ids = self.hn_api.get_ask_stories(max_stories_per_type)
                else:
                    continue

                # Get story details with comments
                stories = []
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_id = {
                        executor.submit(self.hn_api.get_story_with_comments, sid, max_comments_per_story): sid
                        for sid in story_ids
                    }

                    for future in as_completed(future_to_id):
                        story = future.result()
                        if story:
                            story["story_type"] = story_type
                            stories.append(story)

                all_stories.extend(stories)
                logger.info("Collected stories", story_type=story_type, count=len(stories))

            raw_data = {
                "source": "hackernews",
                "query": config.query,
                "total_stories": len(all_stories),
                "stories": all_stories,
                "collection_metadata": {
                    "story_types": story_types,
                    "max_stories_per_type": max_stories_per_type,
                    "max_comments_per_story": max_comments_per_story,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                },
            }

            logger.info("Hacker News data collection completed", total_stories=len(all_stories))
            return raw_data

        except Exception as e:
            logger.error("Hacker News data collection failed", error=str(e))
            raise

    async def run_research(self, config: ResearchConfig) -> ResearchResult:
        """Run complete research workflow with enhanced analysis"""
        logger.info("Starting Hacker News research", query=config.query)

        try:
            # Step 1: Collect raw data
            raw_data = await self.collect_raw_data(config)

            # Step 2: Create result object
            result = ResearchResult(
                id=f"{self.session_id}_{hash(config.query)}",
                source=self.source,
                query=config.query,
                raw_data=raw_data,
                workspace_id=config.workspace_id,
                user_id=config.user_id,
                metadata={
                    "session_id": self.session_id,
                    "analysis_depth": config.analysis_depth.value,
                    "max_items": config.max_items,
                },
            )

            # Step 3: Enhanced AI analysis for Hacker News
            if config.analysis_depth != AnalysisDepth.BASIC:
                analyzed_data = await self._analyze_hackernews_data(raw_data, config)
                result.analyzed_data = analyzed_data

            # Step 4: Save to database
            await self.db_manager.save_research_result(result)

            # Step 5: Save to local file (Hacker News-specific feature)
            await self._save_local_results(result)

            logger.info("Hacker News research completed", result_id=result.id)
            return result

        except Exception as e:
            logger.error("Hacker News research failed", error=str(e))
            raise

    async def _analyze_hackernews_data(self, raw_data: Dict[str, Any], config: ResearchConfig) -> Dict[str, Any]:
        """Enhanced Hacker News-specific analysis using Pydantic AI"""
        try:
            stories = raw_data.get("stories", [])

            # Analyze each story with AI
            analyzed_stories = []

            for story in stories:
                try:
                    title = story.get("title", "")
                    text = story.get("text", "")
                    url = story.get("url", "")
                    story_type = story.get("story_type", "unknown")
                    comments = story.get("comments", [])

                    # Prepare content for analysis
                    story_content = f"""
Story Type: {story_type}
Title: {title}
URL: {url}
Content: {text}
Score: {story.get('score', 0)}
Comments Count: {story.get('descendants', 0)}
"""

                    if comments:
                        comments_text = []
                        for comment in comments[:3]:  # Analyze top 3 comments
                            comment_text = f"Comment by {comment.get('by', 'Unknown')}: {comment.get('text', '')[:300]}"
                            comments_text.append(comment_text)
                        story_content += f"\n\nTop Comments:\n" + "\n---\n".join(comments_text)

                    # Use the standardized agent for analysis
                    analysis = await self.agent.analyze_data({"content": story_content, "story_info": story}, config)

                    analyzed_story = {
                        **story,
                        "ai_analysis": analysis,
                        "analyzed_at": datetime.now(timezone.utc).isoformat(),
                    }

                    analyzed_stories.append(analyzed_story)

                except Exception as e:
                    logger.error("Failed to analyze story", error=str(e))
                    analyzed_stories.append(
                        {
                            **story,
                            "ai_analysis": {"error": str(e)},
                            "analyzed_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            # Generate summary
            summary = self._generate_summary(analyzed_stories)

            return {
                "analyzed_stories": analyzed_stories,
                "summary": summary,
                "analysis_metadata": {
                    "total_stories_analyzed": len(analyzed_stories),
                    "analysis_depth": config.analysis_depth.value,
                    "model_used": self.agent.model_name,
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                },
            }

        except Exception as e:
            logger.error("Hacker News data analysis failed", error=str(e))
            return {"error": str(e), "analyzed_at": datetime.now(timezone.utc).isoformat()}

    def _generate_summary(self, analyzed_stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not analyzed_stories:
            return {"error": "No stories to analyze"}

        # Filter successfully analyzed stories
        successful_analyses = []
        for story in analyzed_stories:
            analysis = story.get("ai_analysis", {})
            if isinstance(analysis, dict) and "error" not in analysis:
                successful_analyses.append(story)

        if not successful_analyses:
            return {
                "total_stories": len(analyzed_stories),
                "analyzed_stories": 0,
                "message": "No stories were successfully analyzed",
            }

        # Calculate statistics
        story_types = []
        total_score = 0
        total_comments = 0

        for story in analyzed_stories:
            story_types.append(story.get("story_type", "unknown"))
            total_score += story.get("score", 0)
            total_comments += story.get("descendants", 0)

        # Extract insights from successful analyses
        all_tools = []
        all_topics = []
        sentiments = []

        for story in successful_analyses:
            analysis = story.get("ai_analysis", {})
            if "analysis" in analysis and isinstance(analysis["analysis"], dict):
                data = analysis["analysis"]
                if data.get("mentioned_tools"):
                    all_tools.extend(data["mentioned_tools"])
                if data.get("key_topics"):
                    all_topics.extend(data["key_topics"])
                if data.get("sentiment"):
                    sentiments.append(data["sentiment"])

        return {
            "total_stories": len(analyzed_stories),
            "analyzed_stories": len(successful_analyses),
            "total_score": total_score,
            "total_comments": total_comments,
            "story_type_distribution": {st: story_types.count(st) for st in set(story_types)} if story_types else {},
            "sentiment_distribution": {s: sentiments.count(s) for s in set(sentiments)} if sentiments else {},
            "top_tools_mentioned": list(set(all_tools))[:10] if all_tools else [],
            "top_topics": list(set(all_topics))[:10] if all_topics else [],
            "analysis_success_rate": len(successful_analyses) / len(analyzed_stories) if analyzed_stories else 0,
        }

    async def _save_local_results(self, result: ResearchResult) -> None:
        """Save results to local file (Hacker News-specific feature)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"standardized_hackernews_research_{timestamp}.json"
            filepath = self.results_dir / filename

            with open(filepath, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)

            logger.info("Results saved to local file", filepath=str(filepath))

        except Exception as e:
            logger.error("Failed to save local results", error=str(e))


# CLI Interface
async def main():
    """Main CLI function"""
    await run_standardized_cli(HackerNewsResearchTool, DataSource.HACKERNEWS)


if __name__ == "__main__":
    exit(asyncio.run(main()))
