#!/usr/bin/env python3
"""
Multi-Source Research Orchestrator
Scalable system for orchestrating research across multiple content sources
"""

import asyncio
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from cli_reddit_analyzer import RedditAIAnalyzer
from cli_reddit_scraper_raw import RawRedditScraperCLI
from user_research_config import ContentSource, UserResearchConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SourceStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SourceResult:
    """Result from a single content source"""

    source: ContentSource
    status: SourceStatus
    started_at: str
    completed_at: Optional[str] = None
    raw_data_path: Optional[str] = None
    analyzed_data_path: Optional[str] = None
    metrics: Dict[str, Any] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class OrchestrationResult:
    """Complete orchestration result"""

    user_id: str
    config_name: str
    job_id: str
    started_at: str
    completed_at: Optional[str] = None
    total_sources: int = 0
    successful_sources: int = 0
    failed_sources: int = 0
    source_results: List[SourceResult] = None
    consolidated_insights: Dict[str, Any] = None

    def __post_init__(self):
        if self.source_results is None:
            self.source_results = []


class ContentSourceWorker:
    """Base class for content source workers"""

    def __init__(self, source: ContentSource):
        self.source = source
        self.logger = logging.getLogger(f"{__name__}.{source.value}")

    async def collect_raw_data(self, config: UserResearchConfig, job_id: str, output_dir: Path) -> SourceResult:
        """Collect raw data from this source"""
        raise NotImplementedError("Subclasses must implement collect_raw_data")

    async def analyze_data(self, raw_data_path: str, config: UserResearchConfig, job_id: str, output_dir: Path) -> str:
        """Analyze collected raw data"""
        raise NotImplementedError("Subclasses must implement analyze_data")


class RedditWorker(ContentSourceWorker):
    """Reddit content source worker"""

    def __init__(self):
        super().__init__(ContentSource.REDDIT)

    async def collect_raw_data(self, config: UserResearchConfig, job_id: str, output_dir: Path) -> SourceResult:
        """Collect raw data from Reddit"""
        result = SourceResult(source=self.source, status=SourceStatus.RUNNING, started_at=datetime.now().isoformat())

        try:
            if not config.reddit_config:
                result.status = SourceStatus.SKIPPED
                result.error_message = "No Reddit configuration provided"
                result.completed_at = datetime.now().isoformat()
                return result

            self.logger.info(f"Starting Reddit data collection for job {job_id}")

            # Create scraper config
            scraper_config = {
                "session_name": f"MultiSource_{job_id}_Reddit",
                "search_query": " ".join(config.reddit_config.search_topics),
                "subreddits": config.reddit_config.subreddits,
                "max_posts_per_subreddit": config.reddit_config.max_posts_per_subreddit,
                "max_comments_per_post": config.reddit_config.max_comments_per_post,
            }

            # Initialize and run scraper
            scraper = RawRedditScraperCLI()
            scraper.results_dir = output_dir / "reddit_raw"
            scraper.results_dir.mkdir(parents=True, exist_ok=True)

            await scraper.initialize_workers()
            success = await scraper.run_raw_collection_session(scraper_config)

            if success:
                # Find the generated raw data file
                raw_files = list(scraper.results_dir.glob("raw_reddit_dataset_*.json"))
                if raw_files:
                    result.raw_data_path = str(raw_files[0])
                    result.status = SourceStatus.COMPLETED
                    result.metrics = {
                        "subreddits_processed": len(config.reddit_config.subreddits),
                        "max_posts_per_subreddit": config.reddit_config.max_posts_per_subreddit,
                        "data_collection_method": "reddit_api",
                    }
                else:
                    result.status = SourceStatus.FAILED
                    result.error_message = "No raw data file generated"
            else:
                result.status = SourceStatus.FAILED
                result.error_message = "Reddit scraper execution failed"

        except Exception as e:
            self.logger.error(f"Reddit data collection failed: {e}")
            result.status = SourceStatus.FAILED
            result.error_message = str(e)

        result.completed_at = datetime.now().isoformat()
        return result

    async def analyze_data(self, raw_data_path: str, config: UserResearchConfig, job_id: str, output_dir: Path) -> str:
        """Analyze Reddit raw data"""
        try:
            self.logger.info(f"Starting Reddit data analysis for job {job_id}")

            analyzer = RedditAIAnalyzer()
            analyzer.analyzed_data_dir = output_dir / "reddit_analyzed"
            analyzer.analyzed_data_dir.mkdir(parents=True, exist_ok=True)

            # Load and analyze the raw dataset
            raw_dataset = await analyzer.load_raw_dataset(Path(raw_data_path))
            if raw_dataset:
                await analyzer.initialize_ai_client()
                success = await analyzer.analyze_dataset(raw_dataset)

                if success:
                    # Find the generated analyzed data file
                    analyzed_files = list(analyzer.analyzed_data_dir.glob("analyzed_reddit_dataset_*.json"))
                    if analyzed_files:
                        return str(analyzed_files[0])

            return None

        except Exception as e:
            self.logger.error(f"Reddit data analysis failed: {e}")
            return None


class LinkedInWorker(ContentSourceWorker):
    """LinkedIn content source worker (placeholder for future implementation)"""

    def __init__(self):
        super().__init__(ContentSource.LINKEDIN)

    async def collect_raw_data(self, config: UserResearchConfig, job_id: str, output_dir: Path) -> SourceResult:
        """Collect raw data from LinkedIn"""
        result = SourceResult(
            source=self.source,
            status=SourceStatus.SKIPPED,
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            error_message="LinkedIn integration not yet implemented",
        )

        self.logger.info(f"LinkedIn data collection scheduled for job {job_id} (not implemented)")
        return result

    async def analyze_data(self, raw_data_path: str, config: UserResearchConfig, job_id: str, output_dir: Path) -> str:
        """Analyze LinkedIn raw data"""
        self.logger.info("LinkedIn analysis not yet implemented")
        return None


class TwitterWorker(ContentSourceWorker):
    """Twitter content source worker (placeholder for future implementation)"""

    def __init__(self):
        super().__init__(ContentSource.TWITTER)

    async def collect_raw_data(self, config: UserResearchConfig, job_id: str, output_dir: Path) -> SourceResult:
        """Collect raw data from Twitter"""
        result = SourceResult(
            source=self.source,
            status=SourceStatus.SKIPPED,
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            error_message="Twitter integration not yet implemented",
        )

        self.logger.info(f"Twitter data collection scheduled for job {job_id} (not implemented)")
        return result

    async def analyze_data(self, raw_data_path: str, config: UserResearchConfig, job_id: str, output_dir: Path) -> str:
        """Analyze Twitter raw data"""
        self.logger.info("Twitter analysis not yet implemented")
        return None


class MultiSourceOrchestrator:
    """Orchestrates research across multiple content sources"""

    def __init__(self, max_concurrent_sources: int = 3):
        self.max_concurrent_sources = max_concurrent_sources
        self.workers = {
            ContentSource.REDDIT: RedditWorker(),
            ContentSource.LINKEDIN: LinkedInWorker(),
            ContentSource.TWITTER: TwitterWorker(),
            # Add more workers as they're implemented
        }
        self.results_dir = Path(__file__).parent / "orchestrated_results"
        self.results_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def orchestrate_research(self, config: UserResearchConfig, job_id: str = None) -> OrchestrationResult:
        """Orchestrate research across all enabled sources"""

        if job_id is None:
            job_id = f"{config.user_id}_{config.config_name}_{int(time.time())}"

        self.logger.info(f"Starting multi-source research orchestration: {job_id}")

        # Create orchestration result
        result = OrchestrationResult(
            user_id=config.user_id,
            config_name=config.config_name,
            job_id=job_id,
            started_at=datetime.now().isoformat(),
            total_sources=len(config.enabled_sources),
        )

        # Create job output directory
        job_dir = self.results_dir / config.user_id / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Stage 1: Parallel raw data collection
            self.logger.info(f"Stage 1: Raw data collection from {len(config.enabled_sources)} sources")
            source_results = await self._collect_raw_data_parallel(config, job_id, job_dir)
            result.source_results = source_results

            # Stage 2: Parallel data analysis (for successful collections)
            self.logger.info(f"Stage 2: Data analysis for successful collections")
            await self._analyze_data_parallel(config, job_id, job_dir, source_results)

            # Stage 3: Consolidate insights
            self.logger.info(f"Stage 3: Consolidating insights across sources")
            result.consolidated_insights = await self._consolidate_insights(source_results, config)

            # Calculate final metrics
            result.successful_sources = sum(1 for sr in source_results if sr.status == SourceStatus.COMPLETED)
            result.failed_sources = sum(1 for sr in source_results if sr.status == SourceStatus.FAILED)
            result.completed_at = datetime.now().isoformat()

            # Save orchestration result
            await self._save_orchestration_result(result, job_dir)

            self.logger.info(
                f"Orchestration completed: {result.successful_sources}/{result.total_sources} sources successful"
            )

        except Exception as e:
            self.logger.error(f"Orchestration failed: {e}")
            result.completed_at = datetime.now().isoformat()
            # Still save partial results
            await self._save_orchestration_result(result, job_dir)

        return result

    async def _collect_raw_data_parallel(
        self, config: UserResearchConfig, job_id: str, job_dir: Path
    ) -> List[SourceResult]:
        """Collect raw data from all enabled sources in parallel"""

        # Create tasks for each enabled source
        tasks = []
        for source in config.enabled_sources:
            if source in self.workers:
                worker = self.workers[source]
                task = asyncio.create_task(
                    worker.collect_raw_data(config, job_id, job_dir), name=f"collect_{source.value}"
                )
                tasks.append(task)
            else:
                self.logger.warning(f"No worker available for source: {source.value}")

        # Execute tasks with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent_sources)

        async def limited_task(task):
            async with semaphore:
                return await task

        # Wait for all tasks to complete
        results = await asyncio.gather(*[limited_task(task) for task in tasks], return_exceptions=True)

        # Process results and handle exceptions
        source_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create failed result for exception
                source = config.enabled_sources[i]
                failed_result = SourceResult(
                    source=source,
                    status=SourceStatus.FAILED,
                    started_at=datetime.now().isoformat(),
                    completed_at=datetime.now().isoformat(),
                    error_message=str(result),
                )
                source_results.append(failed_result)
            else:
                source_results.append(result)

        return source_results

    async def _analyze_data_parallel(
        self, config: UserResearchConfig, job_id: str, job_dir: Path, source_results: List[SourceResult]
    ):
        """Analyze data from successful collections in parallel"""

        # Create analysis tasks for successful collections
        analysis_tasks = []
        for source_result in source_results:
            if source_result.status == SourceStatus.COMPLETED and source_result.raw_data_path:
                worker = self.workers[source_result.source]
                task = asyncio.create_task(
                    worker.analyze_data(source_result.raw_data_path, config, job_id, job_dir),
                    name=f"analyze_{source_result.source.value}",
                )
                analysis_tasks.append((source_result, task))

        # Execute analysis tasks
        if analysis_tasks:
            semaphore = asyncio.Semaphore(self.max_concurrent_sources)

            async def limited_analysis(source_result, task):
                async with semaphore:
                    try:
                        analyzed_path = await task
                        source_result.analyzed_data_path = analyzed_path
                        if analyzed_path:
                            self.logger.info(f"Analysis completed for {source_result.source.value}")
                        else:
                            self.logger.warning(f"Analysis failed for {source_result.source.value}")
                    except Exception as e:
                        self.logger.error(f"Analysis error for {source_result.source.value}: {e}")

            # Wait for all analysis tasks
            await asyncio.gather(*[limited_analysis(sr, task) for sr, task in analysis_tasks])

    async def _consolidate_insights(
        self, source_results: List[SourceResult], config: UserResearchConfig
    ) -> Dict[str, Any]:
        """Consolidate insights from all successful source analyses"""

        consolidated = {
            "summary": {
                "total_sources": len(source_results),
                "successful_sources": sum(1 for sr in source_results if sr.status == SourceStatus.COMPLETED),
                "sources_with_analysis": sum(1 for sr in source_results if sr.analyzed_data_path),
                "consolidation_timestamp": datetime.now().isoformat(),
            },
            "source_metrics": {},
            "cross_source_insights": {
                "common_topics": [],
                "trending_tools": [],
                "sentiment_patterns": {},
                "engagement_patterns": {},
            },
            "business_intelligence": {
                "market_opportunities": [],
                "competitive_insights": [],
                "user_pain_points": [],
                "emerging_trends": [],
            },
        }

        # Aggregate metrics from each source
        for source_result in source_results:
            source_name = source_result.source.value
            consolidated["source_metrics"][source_name] = {
                "status": source_result.status.value,
                "raw_data_available": bool(source_result.raw_data_path),
                "analysis_available": bool(source_result.analyzed_data_path),
                "metrics": source_result.metrics,
            }

            # If analysis is available, extract key insights
            if source_result.analyzed_data_path:
                try:
                    with open(source_result.analyzed_data_path, "r") as f:
                        analysis_data = json.load(f)

                    # Extract insights based on source type
                    if source_result.source == ContentSource.REDDIT:
                        await self._extract_reddit_insights(analysis_data, consolidated)
                    # Add more source-specific insight extraction as needed

                except Exception as e:
                    self.logger.error(f"Failed to extract insights from {source_name}: {e}")

        return consolidated

    async def _extract_reddit_insights(self, reddit_analysis: Dict, consolidated: Dict):
        """Extract insights from Reddit analysis data"""
        try:
            summary = reddit_analysis.get("analysis_summary", {})
            business_intel = summary.get("business_intelligence", {})

            # Add to consolidated insights
            if business_intel.get("top_tools_mentioned"):
                consolidated["cross_source_insights"]["trending_tools"].extend(business_intel["top_tools_mentioned"])

            if business_intel.get("sentiment_distribution"):
                consolidated["cross_source_insights"]["sentiment_patterns"]["reddit"] = business_intel[
                    "sentiment_distribution"
                ]

            # Extract business intelligence
            analyzed_posts = reddit_analysis.get("analyzed_posts", [])
            for post in analyzed_posts:
                ai_analysis = post.get("ai_analysis", {})
                if ai_analysis and not ai_analysis.get("error"):
                    # Extract actionable insights
                    actionable = ai_analysis.get("actionable_insights", {})
                    if actionable.get("business_opportunities"):
                        consolidated["business_intelligence"]["market_opportunities"].extend(
                            actionable["business_opportunities"]
                        )

                    # Extract market intelligence
                    market_intel = ai_analysis.get("market_intelligence", {})
                    if market_intel.get("user_pain_points"):
                        consolidated["business_intelligence"]["user_pain_points"].extend(
                            market_intel["user_pain_points"]
                        )

        except Exception as e:
            self.logger.error(f"Failed to extract Reddit insights: {e}")

    async def _save_orchestration_result(self, result: OrchestrationResult, job_dir: Path):
        """Save the complete orchestration result"""
        try:
            result_file = job_dir / "orchestration_result.json"
            with open(result_file, "w") as f:
                json.dump(asdict(result), f, indent=2, default=str)

            self.logger.info(f"Orchestration result saved: {result_file}")

        except Exception as e:
            self.logger.error(f"Failed to save orchestration result: {e}")


async def main():
    """CLI interface for the multi-source orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Source Research Orchestrator")
    parser.add_argument("--config-file", required=True, help="Path to user research configuration JSON file")
    parser.add_argument("--job-id", help="Custom job ID (optional)")

    args = parser.parse_args()

    try:
        # Load configuration
        with open(args.config_file, "r") as f:
            config_data = json.load(f)

        config = UserResearchConfig(**config_data)

        # Create and run orchestrator
        orchestrator = MultiSourceOrchestrator()
        result = await orchestrator.orchestrate_research(config, args.job_id)

        print(f"✅ Orchestration completed: {result.job_id}")
        print(f"   Successful sources: {result.successful_sources}/{result.total_sources}")
        print(f"   Duration: {result.started_at} to {result.completed_at}")

    except Exception as e:
        print(f"❌ Orchestration failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
