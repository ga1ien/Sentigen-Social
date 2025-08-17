"""
Enhanced Reddit AI Research Worker for AI Business Automation Tools.
Focuses on finding discussions about tools like Cassidy, ClickUp, Glean, Lindy, Gumloop.
Integrates with Supabase for data storage and AI analysis.
"""

import asyncio
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import structlog
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from core.openai_client import GPT5MiniClient
from database.supabase_client import SupabaseClient
from workers.reddit_worker import RedditWorker, WorkerResult, WorkerTask

load_dotenv()

logger = structlog.get_logger(__name__)


class RedditAIResearchWorker(RedditWorker):
    """Enhanced Reddit worker specialized for AI automation tools research with Supabase integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.worker_name = "reddit_ai_research_worker"
        self.supabase_client = SupabaseClient()
        self.openai_client = GPT5MiniClient()
        self._initialize_ai_client()

        # AI automation tools to focus on
        self.target_tools = [
            "cassidy",
            "cassidy.ai",
            "clickup",
            "click up",
            "glean",
            "glean.com",
            "lindy",
            "lindy.ai",
            "gumloop",
            "gum loop",
            "zapier",
            "make.com",
            "integromat",
            "notion ai",
            "airtable",
            "monday.com",
        ]

        # Relevant subreddits for AI automation discussions
        self.target_subreddits = [
            "artificial",
            "MachineLearning",
            "OpenAI",
            "ChatGPT",
            "automation",
            "productivity",
            "Entrepreneur",
            "startups",
            "SaaS",
            "nocode",
            "workflow",
            "business",
            "smallbusiness",
            "digitalnomad",
            "remotework",
            "freelance",
        ]

        logger.info("Reddit AI Research Worker initialized with Supabase integration")

    def _initialize_ai_client(self):
        """Initialize OpenAI GPT-5 Mini client for content analysis."""
        try:
            # Verify OpenAI client is working
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")

            # Set the model to GPT-5 Mini as specified
            self.ai_model = "gpt-5-mini"

            logger.info("OpenAI GPT-5 Mini client initialized successfully for Reddit analysis")

        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            self.openai_client = None

    async def create_research_session(
        self,
        workspace_id: str,
        user_id: str,
        session_name: str,
        search_query: str,
        subreddits: List[str] = None,
        ai_analysis_prompt: str = None,
    ) -> Optional[str]:
        """Create a new Reddit research session in Supabase."""
        try:
            session_data = {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "session_name": session_name,
                "search_query": search_query,
                "search_parameters": {
                    "subreddits": subreddits or self.target_subreddits,
                    "target_tools": self.target_tools,
                    "time_filter": "week",
                    "sort_by": "relevance",
                },
                "status": "pending",
                "ai_analysis_prompt": ai_analysis_prompt
                or "Analyze for AI automation tool discussions and business insights",
                "session_metadata": {"worker_version": "1.0", "created_by": "reddit_ai_research_worker"},
            }

            result = (
                self.supabase_client.service_client.table("reddit_research_sessions").insert(session_data).execute()
            )

            if result.data:
                session_id = result.data[0]["id"]
                logger.info("Research session created", session_id=session_id, session_name=session_name)
                return session_id

            return None

        except Exception as e:
            logger.error("Failed to create research session", error=str(e))
            return None

    async def update_session_status(
        self, session_id: str, status: str, progress: float = None, error_message: str = None
    ) -> bool:
        """Update research session status."""
        try:
            updates = {"status": status}

            if progress is not None:
                updates["progress"] = progress

            if status == "running" and not updates.get("started_at"):
                updates["started_at"] = datetime.utcnow().isoformat()
            elif status == "completed":
                updates["completed_at"] = datetime.utcnow().isoformat()
                updates["progress"] = 1.0

            if error_message:
                updates["error_message"] = error_message

            result = (
                self.supabase_client.service_client.table("reddit_research_sessions")
                .update(updates)
                .eq("id", session_id)
                .execute()
            )

            return bool(result.data)

        except Exception as e:
            logger.error("Failed to update session status", session_id=session_id, error=str(e))
            return False

    async def store_reddit_post(
        self, session_id: str, workspace_id: str, post_data: Dict[str, Any], ai_analysis: Dict[str, Any] = None
    ) -> Optional[str]:
        """Store Reddit post data in Supabase."""
        try:
            # Extract mentioned tools from title and content
            mentioned_tools = self._extract_mentioned_tools(
                f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
            )

            db_post_data = {
                "session_id": session_id,
                "workspace_id": workspace_id,
                "reddit_id": post_data.get("id"),
                "content_type": "post",
                "subreddit": post_data.get("subreddit"),
                "title": post_data.get("title"),
                "author": post_data.get("author"),
                "content_text": post_data.get("selftext", ""),
                "url": post_data.get("url"),
                "permalink": post_data.get("permalink"),
                "score": post_data.get("score", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0),
                "num_comments": post_data.get("num_comments", 0),
                "created_utc": post_data.get("created_utc"),
                "is_video": post_data.get("is_video", False),
                "domain": post_data.get("domain"),
                "flair_text": post_data.get("flair_text"),
                "gilded": post_data.get("gilded", 0),
                "awards": post_data.get("awards", 0),
                "over_18": post_data.get("over_18", False),
                "ai_analysis": ai_analysis or {},
                "relevance_score": ai_analysis.get("relevance_score", 0) if ai_analysis else 0,
                "sentiment_score": ai_analysis.get("sentiment_score") if ai_analysis else None,
                "sentiment_label": ai_analysis.get("sentiment", "neutral") if ai_analysis else "neutral",
                "confidence_score": ai_analysis.get("confidence_score", 0) if ai_analysis else 0,
                "key_topics": ai_analysis.get("key_topics", []) if ai_analysis else [],
                "mentioned_keywords": mentioned_tools,
                "extracted_entities": ai_analysis.get("extracted_entities", {}) if ai_analysis else {},
                "key_insights": ai_analysis.get("key_insights", []) if ai_analysis else [],
                "business_context": ai_analysis.get("business_context") if ai_analysis else None,
                "actionable_intelligence": ai_analysis.get("actionable_intelligence") if ai_analysis else None,
                "content_metadata": {"original_data": post_data, "extraction_timestamp": datetime.utcnow().isoformat()},
                "processing_metadata": {"model_used": "gpt-5-mini", "processed_at": datetime.utcnow().isoformat()},
            }

            result = self.supabase_client.service_client.table("reddit_content").insert(db_post_data).execute()

            if result.data:
                post_id = result.data[0]["id"]
                logger.debug("Reddit post stored", post_id=post_id, reddit_id=post_data.get("id"))
                return post_id

            return None

        except Exception as e:
            logger.error("Failed to store Reddit post", reddit_id=post_data.get("id"), error=str(e))
            return None

    async def store_reddit_comments(
        self, post_id: str, session_id: str, workspace_id: str, comments: List[Dict[str, Any]]
    ) -> List[str]:
        """Store Reddit comments in Supabase."""
        stored_comment_ids = []

        for comment in comments:
            try:
                mentioned_tools = self._extract_mentioned_tools(comment.get("body", ""))

                comment_data = {
                    "parent_id": post_id,
                    "session_id": session_id,
                    "workspace_id": workspace_id,
                    "reddit_id": comment.get("id"),
                    "content_type": "comment",
                    "subreddit": "unknown",  # Comments don't have subreddit in API response
                    "author": comment.get("author"),
                    "content_text": comment.get("body"),
                    "score": comment.get("score", 0),
                    "created_utc": comment.get("created_utc"),
                    "gilded": comment.get("gilded", 0),
                    "awards": comment.get("awards", 0),
                    "mentioned_keywords": mentioned_tools,
                    "content_metadata": {
                        "original_data": comment,
                        "extraction_timestamp": datetime.utcnow().isoformat(),
                    },
                    "processing_metadata": {"model_used": "gpt-5-mini", "processed_at": datetime.utcnow().isoformat()},
                }

                result = self.supabase_client.service_client.table("reddit_content").insert(comment_data).execute()

                if result.data:
                    stored_comment_ids.append(result.data[0]["id"])

            except Exception as e:
                logger.error("Failed to store comment", comment_id=comment.get("id"), error=str(e))
                continue

        return stored_comment_ids

    def _extract_mentioned_tools(self, text: str) -> List[str]:
        """Extract mentioned AI automation tools from text."""
        if not text:
            return []

        text_lower = text.lower()
        mentioned = []

        for tool in self.target_tools:
            if tool.lower() in text_lower:
                # Extract the base tool name (remove .com, .ai suffixes)
                base_name = tool.split(".")[0].split()[0]
                if base_name not in mentioned:
                    mentioned.append(base_name)

        return mentioned

    async def analyze_content_with_ai(self, content: str, context: str = "reddit_post") -> Optional[Dict[str, Any]]:
        """Analyze content using GPT-5 Mini for insights."""
        if not self.openai_client or not content.strip():
            return None

        try:
            system_prompt = """You are an expert AI business automation analyst. Analyze Reddit content for AI automation tool insights.

Focus on:
1. Tool mentions and usage patterns
2. User sentiment (positive, negative, neutral)
3. Business use cases and ROI discussions
4. Implementation challenges and solutions
5. Emerging trends in AI automation

Respond with ONLY valid JSON in this exact format:
{
    "relevance_score": 0.8,
    "sentiment": "positive",
    "mentioned_tools": ["tool1", "tool2"],
    "key_insights": ["insight1", "insight2"],
    "business_context": "description of business use case",
    "actionable_intelligence": "what businesses can learn"
}"""

            user_prompt = f"""Analyze this {context} for AI automation tool insights:

Content: {content[:2000]}

Provide analysis as JSON only."""

            # Use GPT-5 Mini for analysis
            response = await self.openai_client.client.chat.completions.create(
                **self.openai_client.normalize_chat_params(
                    {
                        "model": self.ai_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000,
                    }
                )
            )

            if response and response.choices:
                analysis_text = response.choices[0].message.content.strip()

                # Try to parse JSON from the response
                try:
                    # Clean the response and extract JSON
                    json_match = re.search(r"\{.*\}", analysis_text, re.DOTALL)
                    if json_match:
                        analysis_json = json.loads(json_match.group())

                        # Validate required fields
                        required_fields = [
                            "relevance_score",
                            "sentiment",
                            "mentioned_tools",
                            "key_insights",
                            "business_context",
                            "actionable_intelligence",
                        ]
                        if all(field in analysis_json for field in required_fields):
                            return analysis_json

                except json.JSONDecodeError as e:
                    logger.warning("Failed to parse JSON from AI response", error=str(e))

            # Fallback: create structured analysis from extracted tools
            mentioned_tools = self._extract_mentioned_tools(content)
            return {
                "relevance_score": 0.7 if mentioned_tools else 0.3,
                "sentiment": "neutral",
                "mentioned_tools": mentioned_tools,
                "key_insights": [f"Discussion about AI automation tools in {context}"],
                "business_context": "AI automation and productivity discussion",
                "actionable_intelligence": "Users discussing AI tool implementations and experiences",
            }

        except Exception as e:
            logger.error("Failed to analyze content with GPT-5 Mini", error=str(e))
            return None

    async def research_ai_automation_tools(
        self,
        workspace_id: str,
        user_id: str,
        session_name: str,
        search_query: str = "AI automation tools business",
        subreddits: List[str] = None,
        max_posts_per_subreddit: int = 10,
        include_comments: bool = True,
        ai_analysis_prompt: str = None,
    ) -> Optional[str]:
        """
        Comprehensive research session for AI automation tools.

        Args:
            workspace_id: Workspace ID
            user_id: User ID
            session_name: Name for this research session
            search_query: Search query for Reddit
            subreddits: List of subreddits to search (defaults to AI/business subreddits)
            max_posts_per_subreddit: Maximum posts to collect per subreddit
            include_comments: Whether to collect and analyze comments
            ai_analysis_prompt: Custom prompt for AI analysis

        Returns:
            Session ID if successful, None otherwise
        """
        # Create research session
        session_id = await self.create_research_session(
            workspace_id=workspace_id,
            user_id=user_id,
            session_name=session_name,
            search_query=search_query,
            subreddits=subreddits,
            ai_analysis_prompt=ai_analysis_prompt,
        )

        if not session_id:
            return None

        try:
            await self.update_session_status(session_id, "running", 0.1)

            target_subreddits = subreddits or self.target_subreddits
            total_subreddits = len(target_subreddits)
            posts_collected = 0

            logger.info(
                "Starting AI automation tools research",
                session_id=session_id,
                subreddits=target_subreddits,
                search_query=search_query,
            )

            for i, subreddit in enumerate(target_subreddits):
                try:
                    # Update progress
                    progress = 0.1 + (i / total_subreddits) * 0.8
                    await self.update_session_status(session_id, "running", progress)

                    # Search for posts in this subreddit
                    search_results = await self.search_reddit_content(
                        query=search_query, subreddit=subreddit, time_filter="week", limit=max_posts_per_subreddit
                    )

                    if not search_results or not search_results.get("posts"):
                        logger.debug("No posts found", subreddit=subreddit, query=search_query)
                        continue

                    posts = search_results["posts"]
                    logger.info(f"Found {len(posts)} posts in r/{subreddit}")

                    for post in posts:
                        try:
                            # Analyze post content with AI
                            post_content = f"{post.get('title', '')} {post.get('selftext', '')}"
                            ai_analysis = await self.analyze_content_with_ai(post_content, "reddit_post")

                            # Only store posts with decent relevance score
                            if ai_analysis and ai_analysis.get("relevance_score", 0) >= 0.3:
                                # Store the post
                                post_id = await self.store_reddit_post(
                                    session_id=session_id,
                                    workspace_id=workspace_id,
                                    post_data=post,
                                    ai_analysis=ai_analysis,
                                )

                                if post_id and include_comments and post.get("num_comments", 0) > 0:
                                    # Get and store comments
                                    comments = await self._get_post_comments(post.get("permalink", ""), limit=5)
                                    if comments:
                                        await self.store_reddit_comments(
                                            post_id=post_id,
                                            session_id=session_id,
                                            workspace_id=workspace_id,
                                            comments=comments,
                                        )

                                posts_collected += 1

                                # Small delay to respect rate limits
                                await asyncio.sleep(0.5)

                        except Exception as e:
                            logger.error("Failed to process post", post_id=post.get("id"), error=str(e))
                            continue

                except Exception as e:
                    logger.error("Failed to search subreddit", subreddit=subreddit, error=str(e))
                    continue

            # Update session completion
            await self.update_session_status(session_id, "completed", 1.0)

            # Update session with final stats
            await self._update_session_stats(session_id, posts_collected)

            logger.info(
                "AI automation tools research completed", session_id=session_id, posts_collected=posts_collected
            )

            return session_id

        except Exception as e:
            logger.error("Research session failed", session_id=session_id, error=str(e))
            await self.update_session_status(session_id, "failed", error_message=str(e))
            return None

    async def _update_session_stats(self, session_id: str, posts_collected: int):
        """Update session with final statistics."""
        try:
            updates = {
                "total_posts_found": posts_collected,
                "posts_analyzed": posts_collected,
                "session_metadata": {
                    "completion_timestamp": datetime.utcnow().isoformat(),
                    "posts_collected": posts_collected,
                    "worker_version": "1.0",
                },
            }

            self.supabase_client.service_client.table("reddit_research_sessions").update(updates).eq(
                "id", session_id
            ).execute()

        except Exception as e:
            logger.error("Failed to update session stats", session_id=session_id, error=str(e))

    async def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive results for a research session."""
        try:
            # Get session info
            session_result = (
                self.supabase_client.service_client.table("reddit_research_sessions")
                .select("*")
                .eq("id", session_id)
                .execute()
            )

            if not session_result.data:
                return {"error": "Session not found"}

            session = session_result.data[0]

            # Get posts
            posts_result = (
                self.supabase_client.service_client.table("reddit_posts")
                .select("*")
                .eq("session_id", session_id)
                .order("relevance_score", desc=True)
                .execute()
            )

            posts = posts_result.data or []

            # Get comments count
            comments_result = (
                self.supabase_client.service_client.table("reddit_comments")
                .select("id", count="exact")
                .eq("session_id", session_id)
                .execute()
            )

            comments_count = comments_result.count or 0

            # Aggregate insights
            mentioned_tools = set()
            total_score = 0
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

            for post in posts:
                if post.get("mentioned_tools"):
                    mentioned_tools.update(post["mentioned_tools"])

                total_score += post.get("score", 0)

                ai_analysis = post.get("ai_analysis", {})
                sentiment = ai_analysis.get("sentiment", "neutral")
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

            return {
                "session": session,
                "posts": posts,
                "statistics": {
                    "total_posts": len(posts),
                    "total_comments": comments_count,
                    "total_score": total_score,
                    "average_score": total_score / len(posts) if posts else 0,
                    "mentioned_tools": list(mentioned_tools),
                    "sentiment_distribution": sentiment_counts,
                    "top_posts": posts[:5],  # Top 5 by relevance
                },
            }

        except Exception as e:
            logger.error("Failed to get session results", session_id=session_id, error=str(e))
            return {"error": str(e)}

    async def generate_session_insights(self, session_id: str) -> Optional[str]:
        """Generate AI insights summary for a research session."""
        try:
            session_results = await self.get_session_results(session_id)

            if "error" in session_results:
                return None

            posts = session_results.get("posts", [])
            stats = session_results.get("statistics", {})

            if not posts:
                return None

            # Prepare content for AI analysis
            top_posts_content = []
            for post in posts[:10]:  # Top 10 posts
                ai_analysis = post.get("ai_analysis", {})
                top_posts_content.append(
                    {
                        "title": post.get("title"),
                        "subreddit": post.get("subreddit"),
                        "score": post.get("score"),
                        "insights": ai_analysis.get("key_insights", []),
                        "mentioned_tools": post.get("mentioned_tools", []),
                    }
                )

            system_prompt = """You are an expert business intelligence analyst specializing in AI automation tools. Generate comprehensive insights from Reddit research data."""

            user_prompt = f"""Generate comprehensive insights from this Reddit AI automation tools research:

Session Statistics:
- Total posts analyzed: {stats.get('total_posts')}
- Tools mentioned: {', '.join(stats.get('mentioned_tools', []))}
- Sentiment distribution: {stats.get('sentiment_distribution')}

Top Posts Analysis:
{json.dumps(top_posts_content, indent=2)}

Please provide:
1. Key trends in AI automation tool adoption
2. Most discussed tools and their use cases
3. Common challenges and solutions mentioned
4. Business opportunities identified
5. Actionable recommendations for businesses

Format as a comprehensive business intelligence report."""

            if self.openai_client:
                response = await self.openai_client.client.chat.completions.create(
                    **self.openai_client.normalize_chat_params(
                        {
                            "model": self.ai_model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "temperature": 0.4,
                            "max_tokens": 2000,
                        }
                    )
                )

                if response and response.choices:
                    insights_text = response.choices[0].message.content.strip()
                else:
                    insights_text = "Failed to generate insights with GPT-5 Mini"

                # Store insights in database
                insight_data = {
                    "session_id": session_id,
                    "workspace_id": session_results["session"]["workspace_id"],
                    "user_id": session_results["session"]["user_id"],
                    "insight_type": "comprehensive_analysis",
                    "title": f"AI Automation Tools Research Insights - {session_results['session']['session_name']}",
                    "summary": insights_text[:500] + "..." if len(insights_text) > 500 else insights_text,
                    "detailed_analysis": {
                        "full_analysis": insights_text,
                        "statistics": stats,
                        "generation_timestamp": datetime.utcnow().isoformat(),
                    },
                    "confidence_score": 0.8,
                    "generated_by": "reddit_ai_research_worker",
                }

                result = (
                    self.supabase_client.service_client.table("reddit_research_insights").insert(insight_data).execute()
                )

                if result.data:
                    insight_id = result.data[0]["id"]
                    logger.info("Session insights generated", session_id=session_id, insight_id=insight_id)
                    return insight_id

            return None

        except Exception as e:
            logger.error("Failed to generate session insights", session_id=session_id, error=str(e))
            return None
