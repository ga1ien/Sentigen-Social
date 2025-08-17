#!/usr/bin/env python3
"""
Standardized GitHub Research Tool
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
import base64
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
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


class GitHubAPI:
    """GitHub API client with rate limiting"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Standardized-GitHub-Research-Tool/1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Rate limiting info
        self.rate_limit_remaining = 5000 if self.token else 60
        self.rate_limit_reset = None

    def _check_rate_limit(self, response: requests.Response):
        """Update rate limit info from response headers"""
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in response.headers:
            self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])

    def _wait_for_rate_limit(self):
        """Wait if rate limit is exceeded"""
        import time

        if self.rate_limit_remaining <= 5:  # Conservative buffer
            if self.rate_limit_reset:
                wait_time = max(0, self.rate_limit_reset - time.time() + 1)
                if wait_time > 0:
                    logger.info("Rate limit low, waiting", wait_time=wait_time)
                    time.sleep(wait_time)

    def search_repositories(
        self, query: str, sort: str = "stars", order: str = "desc", per_page: int = 30
    ) -> List[Dict]:
        """Search GitHub repositories"""
        try:
            self._wait_for_rate_limit()

            url = f"{self.base_url}/search/repositories"
            params = {"q": query, "sort": sort, "order": order, "per_page": min(per_page, 100)}  # GitHub max is 100

            response = self.session.get(url, params=params, timeout=30)
            self._check_rate_limit(response)

            if response.status_code == 200:
                return response.json().get("items", [])
            elif response.status_code == 403:
                logger.warning("GitHub API rate limit exceeded or forbidden")
                return []
            else:
                logger.error("GitHub search failed", status_code=response.status_code)
                return []

        except Exception as e:
            logger.error("GitHub search error", error=str(e))
            return []

    def get_repository_readme(self, owner: str, repo: str) -> Optional[str]:
        """Get repository README content"""
        try:
            self._wait_for_rate_limit()

            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            response = self.session.get(url, timeout=30)
            self._check_rate_limit(response)

            if response.status_code == 200:
                readme_data = response.json()
                if readme_data.get("content"):
                    # Decode base64 content
                    content = base64.b64decode(readme_data["content"]).decode("utf-8")
                    return content

            return None

        except Exception as e:
            logger.error("Failed to get README", error=str(e), owner=owner, repo=repo)
            return None

    def get_repository_issues(self, owner: str, repo: str, limit: int = 10) -> List[Dict]:
        """Get repository issues"""
        try:
            self._wait_for_rate_limit()

            url = f"{self.base_url}/repos/{owner}/{repo}/issues"
            params = {"state": "open", "sort": "created", "direction": "desc", "per_page": min(limit, 100)}

            response = self.session.get(url, params=params, timeout=30)
            self._check_rate_limit(response)

            if response.status_code == 200:
                return response.json()

            return []

        except Exception as e:
            logger.error("Failed to get issues", error=str(e), owner=owner, repo=repo)
            return []


class GitHubResearchTool(StandardizedResearchTool):
    """Standardized GitHub research tool implementation"""

    def __init__(self):
        super().__init__(DataSource.GITHUB)
        self.github_api = None
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the GitHub research tool"""
        await super().initialize()

        try:
            logger.info("Initializing GitHub research tool")

            # Initialize GitHub API client
            self.github_api = GitHubAPI()

            logger.info("GitHub research tool initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize GitHub research tool", error=str(e))
            raise

    async def collect_raw_data(self, config: ResearchConfig) -> Dict[str, Any]:
        """Collect raw data from GitHub"""
        try:
            logger.info("Starting GitHub data collection", query=config.query)

            # Parse search parameters
            search_query = config.query
            max_repos = config.max_items
            include_readme = config.custom_parameters.get("include_readme", True)
            include_issues = config.custom_parameters.get("include_issues", True)
            sort_by = config.custom_parameters.get("sort_by", "stars")

            # Search repositories
            repositories = self.github_api.search_repositories(query=search_query, sort=sort_by, per_page=max_repos)

            logger.info("Found repositories", count=len(repositories))

            # Enhance repository data
            enhanced_repos = []

            for repo in repositories:
                try:
                    owner = repo.get("owner", {}).get("login", "")
                    name = repo.get("name", "")

                    if not owner or not name:
                        continue

                    logger.debug("Processing repository", owner=owner, name=name)

                    enhanced_repo = {
                        "basic_info": {
                            "id": repo.get("id"),
                            "name": name,
                            "full_name": repo.get("full_name"),
                            "owner": owner,
                            "description": repo.get("description"),
                            "url": repo.get("html_url"),
                            "clone_url": repo.get("clone_url"),
                            "language": repo.get("language"),
                            "created_at": repo.get("created_at"),
                            "updated_at": repo.get("updated_at"),
                            "pushed_at": repo.get("pushed_at"),
                            "size": repo.get("size"),
                            "stargazers_count": repo.get("stargazers_count", 0),
                            "watchers_count": repo.get("watchers_count", 0),
                            "forks_count": repo.get("forks_count", 0),
                            "open_issues_count": repo.get("open_issues_count", 0),
                            "topics": repo.get("topics", []),
                            "license": repo.get("license", {}).get("name") if repo.get("license") else None,
                            "default_branch": repo.get("default_branch"),
                            "archived": repo.get("archived", False),
                            "disabled": repo.get("disabled", False),
                        },
                        "readme_content": None,
                        "recent_issues": [],
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                    }

                    # Get README if requested
                    if include_readme:
                        readme = self.github_api.get_repository_readme(owner, name)
                        if readme:
                            enhanced_repo["readme_content"] = readme[:5000]  # Limit size

                    # Get recent issues if requested
                    if include_issues:
                        issues = self.github_api.get_repository_issues(owner, name, limit=5)
                        enhanced_repo["recent_issues"] = issues

                    enhanced_repos.append(enhanced_repo)

                except Exception as e:
                    logger.error("Failed to process repository", error=str(e), repo=repo.get("full_name"))
                    continue

            raw_data = {
                "source": "github",
                "query": search_query,
                "total_repositories": len(enhanced_repos),
                "repositories": enhanced_repos,
                "collection_metadata": {
                    "max_repos": max_repos,
                    "sort_by": sort_by,
                    "include_readme": include_readme,
                    "include_issues": include_issues,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                },
            }

            logger.info("GitHub data collection completed", total_repositories=len(enhanced_repos))
            return raw_data

        except Exception as e:
            logger.error("GitHub data collection failed", error=str(e))
            raise

    async def run_research(self, config: ResearchConfig) -> ResearchResult:
        """Run complete research workflow with enhanced analysis"""
        logger.info("Starting GitHub research", query=config.query)

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

            # Step 3: Enhanced AI analysis for GitHub
            if config.analysis_depth != AnalysisDepth.BASIC:
                analyzed_data = await self._analyze_github_data(raw_data, config)
                result.analyzed_data = analyzed_data

            # Step 4: Save to database
            await self.db_manager.save_research_result(result)

            # Step 5: Save to local file (GitHub-specific feature)
            await self._save_local_results(result)

            logger.info("GitHub research completed", result_id=result.id)
            return result

        except Exception as e:
            logger.error("GitHub research failed", error=str(e))
            raise

    async def _analyze_github_data(self, raw_data: Dict[str, Any], config: ResearchConfig) -> Dict[str, Any]:
        """Enhanced GitHub-specific analysis using Pydantic AI"""
        try:
            repositories = raw_data.get("repositories", [])

            # Analyze each repository with AI
            analyzed_repos = []

            for repo in repositories:
                try:
                    basic_info = repo.get("basic_info", {})
                    readme_content = repo.get("readme_content", "")
                    recent_issues = repo.get("recent_issues", [])

                    # Prepare content for analysis
                    repo_content = f"""
Repository: {basic_info.get('full_name', '')}
Description: {basic_info.get('description', '')}
Language: {basic_info.get('language', '')}
Stars: {basic_info.get('stargazers_count', 0)}
Forks: {basic_info.get('forks_count', 0)}
Topics: {', '.join(basic_info.get('topics', []))}
"""

                    if readme_content:
                        repo_content += f"\nREADME Content:\n{readme_content[:2000]}"

                    if recent_issues:
                        issues_text = []
                        for issue in recent_issues[:3]:  # Analyze top 3 issues
                            issue_text = f"Issue: {issue.get('title', '')} - {issue.get('body', '')[:200]}"
                            issues_text.append(issue_text)
                        repo_content += f"\n\nRecent Issues:\n" + "\n---\n".join(issues_text)

                    # Use the standardized agent for analysis
                    analysis = await self.agent.analyze_data(
                        {"content": repo_content, "repository_info": basic_info}, config
                    )

                    analyzed_repo = {
                        **repo,
                        "ai_analysis": analysis,
                        "analyzed_at": datetime.now(timezone.utc).isoformat(),
                    }

                    analyzed_repos.append(analyzed_repo)

                except Exception as e:
                    logger.error("Failed to analyze repository", error=str(e))
                    analyzed_repos.append(
                        {
                            **repo,
                            "ai_analysis": {"error": str(e)},
                            "analyzed_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            # Generate summary
            summary = self._generate_summary(analyzed_repos)

            return {
                "analyzed_repositories": analyzed_repos,
                "summary": summary,
                "analysis_metadata": {
                    "total_repos_analyzed": len(analyzed_repos),
                    "analysis_depth": config.analysis_depth.value,
                    "model_used": self.agent.model_name,
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                },
            }

        except Exception as e:
            logger.error("GitHub data analysis failed", error=str(e))
            return {"error": str(e), "analyzed_at": datetime.now(timezone.utc).isoformat()}

    def _generate_summary(self, analyzed_repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not analyzed_repos:
            return {"error": "No repositories to analyze"}

        # Filter successfully analyzed repositories
        successful_analyses = []
        for repo in analyzed_repos:
            analysis = repo.get("ai_analysis", {})
            if isinstance(analysis, dict) and "error" not in analysis:
                successful_analyses.append(repo)

        if not successful_analyses:
            return {
                "total_repositories": len(analyzed_repos),
                "analyzed_repositories": 0,
                "message": "No repositories were successfully analyzed",
            }

        # Calculate statistics
        languages = []
        topics = []
        total_stars = 0
        total_forks = 0

        for repo in analyzed_repos:
            basic_info = repo.get("basic_info", {})
            if basic_info.get("language"):
                languages.append(basic_info["language"])
            topics.extend(basic_info.get("topics", []))
            total_stars += basic_info.get("stargazers_count", 0)
            total_forks += basic_info.get("forks_count", 0)

        # Extract insights from successful analyses
        all_tools = []
        all_topics_from_analysis = []

        for repo in successful_analyses:
            analysis = repo.get("ai_analysis", {})
            if "analysis" in analysis and isinstance(analysis["analysis"], dict):
                data = analysis["analysis"]
                if data.get("mentioned_tools"):
                    all_tools.extend(data["mentioned_tools"])
                if data.get("key_topics"):
                    all_topics_from_analysis.extend(data["key_topics"])

        return {
            "total_repositories": len(analyzed_repos),
            "analyzed_repositories": len(successful_analyses),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "language_distribution": {lang: languages.count(lang) for lang in set(languages)} if languages else {},
            "top_repository_topics": list(set(topics))[:10] if topics else [],
            "top_tools_mentioned": list(set(all_tools))[:10] if all_tools else [],
            "top_analysis_topics": list(set(all_topics_from_analysis))[:10] if all_topics_from_analysis else [],
            "analysis_success_rate": len(successful_analyses) / len(analyzed_repos) if analyzed_repos else 0,
        }

    async def _save_local_results(self, result: ResearchResult) -> None:
        """Save results to local file (GitHub-specific feature)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"standardized_github_research_{timestamp}.json"
            filepath = self.results_dir / filename

            with open(filepath, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)

            logger.info("Results saved to local file", filepath=str(filepath))

        except Exception as e:
            logger.error("Failed to save local results", error=str(e))


# CLI Interface
async def main():
    """Main CLI function"""
    await run_standardized_cli(GitHubResearchTool, DataSource.GITHUB)


if __name__ == "__main__":
    exit(asyncio.run(main()))
