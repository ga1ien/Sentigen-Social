"""
Reddit API Worker for content research and social media intelligence.
Uses Reddit API to gather trending content, discussions, and insights.
"""

import asyncio
import base64
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import httpx
import structlog
from dotenv import load_dotenv

from workers.base_worker import BaseWorker, WorkerResult, WorkerTask

load_dotenv()

logger = structlog.get_logger(__name__)


class RedditWorker(BaseWorker):
    """Worker specialized for Reddit API content research and social media intelligence."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("reddit_worker", config)
        self.access_token = None
        self.token_expires_at = None

    def _initialize_config(self):
        """Initialize Reddit API specific configuration."""
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "7dj-umFWDSZvyE9LDj9vyA")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "eWfyYnYy3ZLJDZf5UMJpGtorWmLlMg")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "ContentResearch/1.0 by SentigenSocial")
        self.base_url = "https://www.reddit.com"
        self.oauth_url = "https://www.reddit.com/api/v1/access_token"

        if not self.client_id or not self.client_secret:
            logger.warning("Reddit API credentials not found - reddit worker will be disabled")
            return

        self.config.update(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "user_agent": self.user_agent,
                "base_url": self.base_url,
            }
        )

        logger.info("Reddit worker configuration initialized")

    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token for Reddit API."""
        # Check if we have a valid token
        if self.access_token and self.token_expires_at and datetime.utcnow() < self.token_expires_at:
            return self.access_token

        try:
            # Prepare authentication
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

            headers = {
                "Authorization": f"Basic {auth_b64}",
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {"grant_type": "client_credentials"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.oauth_url, headers=headers, data=data)

                response.raise_for_status()
                token_data = response.json()

                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)

                logger.info("Reddit access token obtained successfully")
                return self.access_token

        except Exception as e:
            logger.error("Failed to get Reddit access token", error=str(e))
            return None

    async def _make_reddit_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Reddit API."""
        access_token = await self._get_access_token()
        if not access_token:
            return None

        headers = {"Authorization": f"Bearer {access_token}", "User-Agent": self.user_agent}

        url = f"https://oauth.reddit.com{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params or {})
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Reddit API request failed", endpoint=endpoint, status_code=e.response.status_code, error=str(e)
            )
            return None
        except Exception as e:
            logger.error("Unexpected error in Reddit API request", endpoint=endpoint, error=str(e))
            return None

    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process a Reddit research task.

        Args:
            task: Reddit research task

        Returns:
            WorkerResult with Reddit data and insights
        """
        if not self.client_id or not self.client_secret:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message="Reddit API credentials not configured",
            )

        try:
            # Extract task parameters
            task_type = task.input_data.get("task_type", "trending_posts")
            subreddit = task.input_data.get("subreddit", "all")
            time_filter = task.input_data.get("time_filter", "day")  # hour, day, week, month, year, all
            sort_by = task.input_data.get("sort_by", "hot")  # hot, new, rising, top
            limit = task.input_data.get("limit", 25)
            search_query = task.input_data.get("search_query")
            include_comments = task.input_data.get("include_comments", False)

            # Process different task types
            if task_type == "trending_posts":
                result_data = await self._get_trending_posts(subreddit, sort_by, time_filter, limit, include_comments)
            elif task_type == "search_posts":
                if not search_query:
                    return WorkerResult(
                        task_id=task.task_id,
                        worker_type=self.worker_name,
                        status="error",
                        result=None,
                        error_message="Search query required for search_posts task",
                    )
                result_data = await self._search_posts(
                    search_query, subreddit, sort_by, time_filter, limit, include_comments
                )
            elif task_type == "subreddit_info":
                result_data = await self._get_subreddit_info(subreddit)
            elif task_type == "user_posts":
                username = task.input_data.get("username")
                if not username:
                    return WorkerResult(
                        task_id=task.task_id,
                        worker_type=self.worker_name,
                        status="error",
                        result=None,
                        error_message="Username required for user_posts task",
                    )
                result_data = await self._get_user_posts(username, sort_by, limit)
            elif task_type == "content_analysis":
                result_data = await self._analyze_content_trends(subreddit, time_filter, limit)
            else:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message=f"Unknown task type: {task_type}",
                )

            if result_data is None:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message="Failed to fetch data from Reddit API",
                )

            # Add metadata
            result_data.update(
                {
                    "task_type": task_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "reddit_api",
                    "worker": self.worker_name,
                }
            )

            logger.info(
                "Reddit research task completed successfully",
                task_id=task.task_id,
                task_type=task_type,
                subreddit=subreddit,
                posts_count=len(result_data.get("posts", [])),
            )

            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="success",
                result=result_data,
                metadata={
                    "task_type": task_type,
                    "subreddit": subreddit,
                    "posts_count": len(result_data.get("posts", [])),
                    "api_source": "reddit",
                },
            )

        except Exception as e:
            logger.error("Reddit research task failed", task_id=task.task_id, error=str(e))

            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Reddit research failed: {str(e)}",
            )

    async def _get_trending_posts(
        self, subreddit: str, sort_by: str, time_filter: str, limit: int, include_comments: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get trending posts from a subreddit."""
        endpoint = f"/r/{subreddit}/{sort_by}"
        params = {"limit": min(limit, 100), "t": time_filter if sort_by == "top" else None}  # Reddit API limit

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        data = await self._make_reddit_request(endpoint, params)
        if not data:
            return None

        posts = []
        for post_data in data.get("data", {}).get("children", []):
            post = post_data.get("data", {})

            processed_post = {
                "id": post.get("id"),
                "title": post.get("title"),
                "author": post.get("author"),
                "subreddit": post.get("subreddit"),
                "score": post.get("score", 0),
                "upvote_ratio": post.get("upvote_ratio", 0),
                "num_comments": post.get("num_comments", 0),
                "created_utc": post.get("created_utc"),
                "url": post.get("url"),
                "permalink": f"https://reddit.com{post.get('permalink', '')}",
                "selftext": post.get("selftext", ""),
                "is_video": post.get("is_video", False),
                "domain": post.get("domain"),
                "flair_text": post.get("link_flair_text"),
                "gilded": post.get("gilded", 0),
                "awards": len(post.get("all_awardings", [])),
                "over_18": post.get("over_18", False),
            }

            # Get comments if requested
            if include_comments and post.get("permalink"):
                comments = await self._get_post_comments(post.get("permalink"))
                processed_post["top_comments"] = comments

            posts.append(processed_post)

        return {
            "subreddit": subreddit,
            "sort_by": sort_by,
            "time_filter": time_filter,
            "posts": posts,
            "total_posts": len(posts),
        }

    async def _search_posts(
        self, query: str, subreddit: str, sort_by: str, time_filter: str, limit: int, include_comments: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Search for posts in a subreddit."""
        endpoint = f"/r/{subreddit}/search"
        params = {
            "q": query,
            "sort": sort_by,
            "t": time_filter,
            "limit": min(limit, 100),
            "restrict_sr": "true",
            "type": "link",
        }

        data = await self._make_reddit_request(endpoint, params)
        if not data:
            return None

        posts = []
        for post_data in data.get("data", {}).get("children", []):
            post = post_data.get("data", {})

            processed_post = {
                "id": post.get("id"),
                "title": post.get("title"),
                "author": post.get("author"),
                "subreddit": post.get("subreddit"),
                "score": post.get("score", 0),
                "upvote_ratio": post.get("upvote_ratio", 0),
                "num_comments": post.get("num_comments", 0),
                "created_utc": post.get("created_utc"),
                "url": post.get("url"),
                "permalink": f"https://reddit.com{post.get('permalink', '')}",
                "selftext": post.get("selftext", ""),
                "is_video": post.get("is_video", False),
                "domain": post.get("domain"),
                "flair_text": post.get("link_flair_text"),
                "gilded": post.get("gilded", 0),
                "awards": len(post.get("all_awardings", [])),
                "over_18": post.get("over_18", False),
            }

            # Get comments if requested
            if include_comments and post.get("permalink"):
                comments = await self._get_post_comments(post.get("permalink"))
                processed_post["top_comments"] = comments

            posts.append(processed_post)

        return {
            "search_query": query,
            "subreddit": subreddit,
            "sort_by": sort_by,
            "time_filter": time_filter,
            "posts": posts,
            "total_posts": len(posts),
        }

    async def _get_subreddit_info(self, subreddit: str) -> Optional[Dict[str, Any]]:
        """Get information about a subreddit."""
        endpoint = f"/r/{subreddit}/about"

        data = await self._make_reddit_request(endpoint)
        if not data:
            return None

        subreddit_data = data.get("data", {})

        return {
            "name": subreddit_data.get("display_name"),
            "title": subreddit_data.get("title"),
            "description": subreddit_data.get("public_description"),
            "subscribers": subreddit_data.get("subscribers", 0),
            "active_users": subreddit_data.get("active_user_count", 0),
            "created_utc": subreddit_data.get("created_utc"),
            "over_18": subreddit_data.get("over18", False),
            "lang": subreddit_data.get("lang"),
            "subreddit_type": subreddit_data.get("subreddit_type"),
            "url": f"https://reddit.com/r/{subreddit}",
        }

    async def _get_user_posts(self, username: str, sort_by: str, limit: int) -> Optional[Dict[str, Any]]:
        """Get posts from a specific user."""
        endpoint = f"/user/{username}/submitted"
        params = {"sort": sort_by, "limit": min(limit, 100)}

        data = await self._make_reddit_request(endpoint, params)
        if not data:
            return None

        posts = []
        for post_data in data.get("data", {}).get("children", []):
            post = post_data.get("data", {})

            processed_post = {
                "id": post.get("id"),
                "title": post.get("title"),
                "subreddit": post.get("subreddit"),
                "score": post.get("score", 0),
                "upvote_ratio": post.get("upvote_ratio", 0),
                "num_comments": post.get("num_comments", 0),
                "created_utc": post.get("created_utc"),
                "url": post.get("url"),
                "permalink": f"https://reddit.com{post.get('permalink', '')}",
                "selftext": post.get("selftext", ""),
                "is_video": post.get("is_video", False),
                "domain": post.get("domain"),
                "flair_text": post.get("link_flair_text"),
                "gilded": post.get("gilded", 0),
                "awards": len(post.get("all_awardings", [])),
                "over_18": post.get("over_18", False),
            }

            posts.append(processed_post)

        return {"username": username, "sort_by": sort_by, "posts": posts, "total_posts": len(posts)}

    async def _get_post_comments(self, permalink: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top comments for a post."""
        endpoint = f"{permalink.rstrip('/')}"
        params = {"limit": limit}

        data = await self._make_reddit_request(endpoint, params)
        if not data or len(data) < 2:
            return []

        comments_data = data[1].get("data", {}).get("children", [])
        comments = []

        for comment_data in comments_data[:limit]:
            comment = comment_data.get("data", {})
            if comment.get("body") and comment.get("body") != "[deleted]":
                comments.append(
                    {
                        "id": comment.get("id"),
                        "author": comment.get("author"),
                        "body": comment.get("body"),
                        "score": comment.get("score", 0),
                        "created_utc": comment.get("created_utc"),
                        "gilded": comment.get("gilded", 0),
                        "awards": len(comment.get("all_awardings", [])),
                    }
                )

        return comments

    async def _analyze_content_trends(self, subreddit: str, time_filter: str, limit: int) -> Optional[Dict[str, Any]]:
        """Analyze content trends in a subreddit."""
        # Get top posts
        trending_data = await self._get_trending_posts(subreddit, "top", time_filter, limit, False)

        if not trending_data:
            return None

        posts = trending_data.get("posts", [])

        # Analyze trends
        total_score = sum(post.get("score", 0) for post in posts)
        total_comments = sum(post.get("num_comments", 0) for post in posts)
        avg_score = total_score / len(posts) if posts else 0
        avg_comments = total_comments / len(posts) if posts else 0

        # Top domains
        domains = {}
        for post in posts:
            domain = post.get("domain", "self")
            domains[domain] = domains.get(domain, 0) + 1

        top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]

        # Top flairs
        flairs = {}
        for post in posts:
            flair = post.get("flair_text")
            if flair:
                flairs[flair] = flairs.get(flair, 0) + 1

        top_flairs = sorted(flairs.items(), key=lambda x: x[1], reverse=True)[:10]

        # Most engaging posts (top 5 by score)
        top_posts = sorted(posts, key=lambda x: x.get("score", 0), reverse=True)[:5]

        return {
            "subreddit": subreddit,
            "time_filter": time_filter,
            "analysis": {
                "total_posts": len(posts),
                "total_score": total_score,
                "total_comments": total_comments,
                "average_score": round(avg_score, 2),
                "average_comments": round(avg_comments, 2),
                "top_domains": top_domains,
                "top_flairs": top_flairs,
                "most_engaging_posts": [
                    {
                        "title": post.get("title"),
                        "score": post.get("score"),
                        "comments": post.get("num_comments"),
                        "url": post.get("permalink"),
                    }
                    for post in top_posts
                ],
            },
            "posts": posts,
        }

    async def health_check(self) -> bool:
        """Check if Reddit API is accessible."""
        if not self.client_id or not self.client_secret:
            self.is_healthy = False
            return False

        try:
            # Test getting access token
            access_token = await self._get_access_token()
            if not access_token:
                self.is_healthy = False
                return False

            # Test simple API call
            data = await self._make_reddit_request("/r/test/hot", {"limit": 1})

            self.is_healthy = data is not None
            self.last_health_check = datetime.utcnow()

            return self.is_healthy

        except Exception as e:
            logger.warning("Reddit worker health check failed", error=str(e))
            self.is_healthy = False
            self.last_health_check = datetime.utcnow()
            return False

    # Convenience methods for common tasks

    async def get_trending_content(
        self, subreddit: str = "all", time_filter: str = "day", limit: int = 25
    ) -> Optional[Dict[str, Any]]:
        """Get trending content from a subreddit."""
        task = WorkerTask(
            task_id=f"trending_{subreddit}_{datetime.utcnow().timestamp()}",
            task_type="trending_content",
            input_data={
                "task_type": "trending_posts",
                "subreddit": subreddit,
                "sort_by": "hot",
                "time_filter": time_filter,
                "limit": limit,
                "include_comments": False,
            },
        )

        result = await self.process_task(task)
        return result.result if result.status == "success" else None

    async def search_reddit_content(
        self, query: str, subreddit: str = "all", time_filter: str = "week", limit: int = 25
    ) -> Optional[Dict[str, Any]]:
        """Search for content on Reddit."""
        task = WorkerTask(
            task_id=f"search_{query}_{datetime.utcnow().timestamp()}",
            task_type="search_content",
            input_data={
                "task_type": "search_posts",
                "search_query": query,
                "subreddit": subreddit,
                "sort_by": "relevance",
                "time_filter": time_filter,
                "limit": limit,
                "include_comments": False,
            },
        )

        result = await self.process_task(task)
        return result.result if result.status == "success" else None

    async def analyze_subreddit_trends(
        self, subreddit: str, time_filter: str = "week", limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Analyze content trends in a subreddit."""
        task = WorkerTask(
            task_id=f"analyze_{subreddit}_{datetime.utcnow().timestamp()}",
            task_type="trend_analysis",
            input_data={
                "task_type": "content_analysis",
                "subreddit": subreddit,
                "time_filter": time_filter,
                "limit": limit,
            },
        )

        result = await self.process_task(task)
        return result.result if result.status == "success" else None

    async def get_user_content_history(
        self, username: str, sort_by: str = "new", limit: int = 25
    ) -> Optional[Dict[str, Any]]:
        """Get content history for a specific user."""
        task = WorkerTask(
            task_id=f"user_{username}_{datetime.utcnow().timestamp()}",
            task_type="user_content",
            input_data={"task_type": "user_posts", "username": username, "sort_by": sort_by, "limit": limit},
        )

        result = await self.process_task(task)
        return result.result if result.status == "success" else None
