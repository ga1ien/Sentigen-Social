#!/usr/bin/env python3
"""
Standardized Reddit Research Tool
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import structlog

from core.openai_client import GPT5MiniClient
from features.STANDARDIZED_TOOL_TEMPLATE import (
    AnalysisDepth,
    DataSource,
    ResearchConfig,
    ResearchResult,
    StandardizedResearchTool,
    run_standardized_cli,
)
from workers.reddit_worker import RedditWorker

logger = structlog.get_logger(__name__)


class RedditResearchTool(StandardizedResearchTool):
    """Standardized Reddit research tool implementation"""

    def __init__(self):
        super().__init__(DataSource.REDDIT)
        self.reddit_worker = None
        self.ai_client = None
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the Reddit research tool"""
        await super().initialize()

        try:
            logger.info("Initializing Reddit research workers")

            # Initialize Reddit worker
            self.reddit_worker = RedditWorker()

            # Test Reddit connection
            token = await self.reddit_worker._get_access_token()
            if not token:
                raise Exception("Failed to connect to Reddit API")

            # Initialize AI client
            self.ai_client = GPT5MiniClient()

            logger.info("Reddit research tool initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Reddit research tool", error=str(e))
            raise

    async def collect_raw_data(self, config: ResearchConfig) -> Dict[str, Any]:
        """Collect raw data from Reddit"""
        try:
            logger.info("Starting Reddit data collection", query=config.query)

            # Parse subreddits from query or use defaults
            subreddits = config.custom_parameters.get("subreddits", ["artificial", "productivity", "Entrepreneur"])
            max_posts_per_subreddit = config.max_items
            max_comments_per_post = config.custom_parameters.get("max_comments_per_post", 5)

            all_posts = []

            # Scrape each subreddit
            for subreddit in subreddits:
                logger.info("Scraping subreddit", subreddit=subreddit)

                posts = await self._scrape_subreddit(subreddit, max_posts_per_subreddit, max_comments_per_post)
                all_posts.extend(posts)

                # Small delay between subreddits
                await asyncio.sleep(1)

            raw_data = {
                "source": "reddit",
                "query": config.query,
                "subreddits": subreddits,
                "total_posts": len(all_posts),
                "posts": all_posts,
                "collection_metadata": {
                    "max_posts_per_subreddit": max_posts_per_subreddit,
                    "max_comments_per_post": max_comments_per_post,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                },
            }

            logger.info("Reddit data collection completed", total_posts=len(all_posts))
            return raw_data

        except Exception as e:
            logger.error("Reddit data collection failed", error=str(e))
            raise

    async def _scrape_subreddit(self, subreddit: str, max_posts: int, max_comments: int) -> List[Dict[str, Any]]:
        """Scrape posts and comments from a specific subreddit"""
        try:
            # Get trending posts
            response = await self.reddit_worker._make_reddit_request(f"/r/{subreddit}/hot", {"limit": max_posts})

            if not response or "data" not in response:
                logger.warning("No data from subreddit", subreddit=subreddit)
                return []

            posts_data = response["data"].get("children", [])
            posts = [child["data"] for child in posts_data if child.get("data")]

            logger.info("Found posts in subreddit", subreddit=subreddit, count=len(posts))

            # Process each post
            processed_posts = []

            for i, post in enumerate(posts, 1):
                try:
                    title = post.get("title", "No title")
                    permalink = post.get("permalink", "")
                    num_comments = post.get("num_comments", 0)

                    logger.debug("Processing post", post_number=i, title=title[:50])

                    # Get comments for this post
                    comments = []
                    if num_comments > 0 and permalink:
                        comments = await self.reddit_worker._get_post_comments(permalink, max_comments)
                        logger.debug("Fetched comments", post_number=i, comment_count=len(comments))

                    processed_post = {
                        "reddit_data": {
                            "id": post.get("id"),
                            "title": title,
                            "author": post.get("author"),
                            "subreddit": post.get("subreddit"),
                            "score": post.get("score", 0),
                            "upvote_ratio": post.get("upvote_ratio"),
                            "num_comments": num_comments,
                            "created_utc": post.get("created_utc"),
                            "url": post.get("url"),
                            "permalink": permalink,
                            "selftext": post.get("selftext", ""),
                            "domain": post.get("domain"),
                            "flair_text": post.get("flair_text"),
                        },
                        "comments": comments,
                        "processed_at": datetime.now(timezone.utc).isoformat(),
                    }

                    processed_posts.append(processed_post)

                except Exception as e:
                    logger.error("Failed to process post", error=str(e), post_number=i)
                    continue

            return processed_posts

        except Exception as e:
            logger.error("Failed to scrape subreddit", error=str(e), subreddit=subreddit)
            return []

    async def run_research(self, config: ResearchConfig) -> ResearchResult:
        """Run complete research workflow with enhanced analysis"""
        logger.info("Starting Reddit research", query=config.query)

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
                    "subreddits": config.custom_parameters.get("subreddits", []),
                },
            )

            # Step 3: Enhanced AI analysis for Reddit
            if config.analysis_depth != AnalysisDepth.BASIC:
                analyzed_data = await self._analyze_reddit_data(raw_data, config)
                result.analyzed_data = analyzed_data

            # Step 4: Save to database
            await self.db_manager.save_research_result(result)

            # Step 5: Save to local file (Reddit-specific feature)
            await self._save_local_results(result)

            logger.info("Reddit research completed", result_id=result.id)
            return result

        except Exception as e:
            logger.error("Reddit research failed", error=str(e))
            raise

    async def _analyze_reddit_data(self, raw_data: Dict[str, Any], config: ResearchConfig) -> Dict[str, Any]:
        """Enhanced Reddit-specific analysis using Pydantic AI"""
        try:
            posts = raw_data.get("posts", [])

            # Analyze each post with AI
            analyzed_posts = []

            for post in posts:
                try:
                    # Prepare content for analysis
                    reddit_data = post.get("reddit_data", {})
                    comments = post.get("comments", [])

                    title = reddit_data.get("title", "")
                    content = reddit_data.get("selftext", "")

                    # Combine post and comments for analysis
                    post_content = f"Title: {title}\nContent: {content}"

                    comments_content = ""
                    if comments:
                        comments_text = []
                        for comment in comments:
                            comment_text = f"Comment by {comment.get('author', 'Unknown')}: {comment.get('body', '')}"
                            comments_text.append(comment_text)
                        comments_content = "\n\nTop Comments:\n" + "\n---\n".join(comments_text)

                    full_content = post_content + comments_content

                    # Use the standardized agent for analysis
                    analysis = await self.agent.analyze_data(
                        {"content": full_content, "has_comments": len(comments) > 0}, config
                    )

                    # Analyze comments individually
                    comment_analyses = []
                    if comments and config.analysis_depth == AnalysisDepth.COMPREHENSIVE:
                        for comment in comments:
                            comment_analysis = await self._analyze_comment(comment.get("body", ""))
                            comment_analyses.append({**comment, "ai_analysis": comment_analysis})

                    analyzed_post = {
                        **post,
                        "ai_analysis": analysis,
                        "comment_analyses": comment_analyses,
                        "analyzed_at": datetime.now(timezone.utc).isoformat(),
                    }

                    analyzed_posts.append(analyzed_post)

                except Exception as e:
                    logger.error("Failed to analyze post", error=str(e))
                    analyzed_posts.append(
                        {
                            **post,
                            "ai_analysis": {"error": str(e)},
                            "comment_analyses": [],
                            "analyzed_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            # Generate summary
            summary = self._generate_summary(analyzed_posts)

            return {
                "analyzed_posts": analyzed_posts,
                "summary": summary,
                "analysis_metadata": {
                    "total_posts_analyzed": len(analyzed_posts),
                    "analysis_depth": config.analysis_depth.value,
                    "model_used": self.agent.model_name,
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                },
            }

        except Exception as e:
            logger.error("Reddit data analysis failed", error=str(e))
            return {"error": str(e), "analyzed_at": datetime.now(timezone.utc).isoformat()}

    async def _analyze_comment(self, comment_text: str) -> Dict[str, Any]:
        """Analyze individual comment using AI"""
        try:
            if not comment_text.strip():
                return {"error": "Empty comment"}

            # Use AI client for comment analysis
            system_prompt = """Analyze this Reddit comment for business insights. Focus on:
1. Sentiment (positive/negative/neutral)
2. Key insights or opinions
3. Mentioned tools or solutions
4. Practical experience or advice

Respond with JSON only:
{
  "sentiment": "positive/negative/neutral",
  "sentiment_score": -1.0 to 1.0,
  "key_insight": "main point or insight from comment",
  "mentioned_tools": ["tool1", "tool2"],
  "has_experience": true/false,
  "advice_given": true/false
}"""

            response = await self.ai_client.client.chat.completions.create(
                **self.ai_client.normalize_chat_params(
                    {
                        "model": "gpt-5-mini",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": comment_text[:1000]},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 300,
                    }
                )
            )

            if response and response.choices:
                analysis_text = response.choices[0].message.content.strip()

                # Try to parse JSON
                try:
                    import re

                    json_match = re.search(r"\{.*\}", analysis_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        return {"error": "No JSON found in response", "raw_response": analysis_text}
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON", "raw_response": analysis_text}

            return {"error": "No response from AI"}

        except Exception as e:
            logger.error("Comment analysis failed", error=str(e))
            return {"error": str(e)}

    def _generate_summary(self, analyzed_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not analyzed_posts:
            return {"error": "No posts to analyze"}

        # Filter successfully analyzed posts
        successful_analyses = []
        for post in analyzed_posts:
            analysis = post.get("ai_analysis", {})
            if isinstance(analysis, dict) and "error" not in analysis:
                successful_analyses.append(post)

        if not successful_analyses:
            return {
                "total_posts": len(analyzed_posts),
                "analyzed_posts": 0,
                "message": "No posts were successfully analyzed",
            }

        # Calculate statistics
        total_comments = sum(len(post.get("comments", [])) for post in analyzed_posts)
        analyzed_comments = []

        for post in analyzed_posts:
            for comment in post.get("comment_analyses", []):
                if (
                    comment.get("ai_analysis")
                    and isinstance(comment["ai_analysis"], dict)
                    and "error" not in comment["ai_analysis"]
                ):
                    analyzed_comments.append(comment)

        # Extract insights from successful analyses
        all_tools = []
        all_topics = []
        sentiments = []

        for post in successful_analyses:
            analysis = post.get("ai_analysis", {})
            if "analysis" in analysis and isinstance(analysis["analysis"], dict):
                data = analysis["analysis"]
                if data.get("mentioned_tools"):
                    all_tools.extend(data["mentioned_tools"])
                if data.get("key_topics"):
                    all_topics.extend(data["key_topics"])
                if data.get("sentiment"):
                    sentiments.append(data["sentiment"])

        return {
            "total_posts": len(analyzed_posts),
            "analyzed_posts": len(successful_analyses),
            "total_comments": total_comments,
            "analyzed_comments": len(analyzed_comments),
            "sentiment_distribution": {s: sentiments.count(s) for s in set(sentiments)} if sentiments else {},
            "top_tools": list(set(all_tools))[:10] if all_tools else [],
            "top_topics": list(set(all_topics))[:10] if all_topics else [],
            "analysis_success_rate": len(successful_analyses) / len(analyzed_posts) if analyzed_posts else 0,
        }

    async def _save_local_results(self, result: ResearchResult) -> None:
        """Save results to local file (Reddit-specific feature)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"standardized_reddit_research_{timestamp}.json"
            filepath = self.results_dir / filename

            with open(filepath, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)

            logger.info("Results saved to local file", filepath=str(filepath))

        except Exception as e:
            logger.error("Failed to save local results", error=str(e))


# CLI Interface
async def main():
    """Main CLI function"""
    await run_standardized_cli(RedditResearchTool, DataSource.REDDIT)


if __name__ == "__main__":
    exit(asyncio.run(main()))
