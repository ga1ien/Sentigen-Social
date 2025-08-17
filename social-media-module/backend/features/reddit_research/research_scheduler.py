#!/usr/bin/env python3
"""
Research Scheduler System
Handles automated scheduling and execution of user research configurations
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import schedule

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from cli_reddit_analyzer import RedditAIAnalyzer
from cli_reddit_scraper_raw import RawRedditScraperCLI
from user_research_config import ResearchFrequency, UserResearchConfig, UserResearchConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("research_scheduler.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ResearchJobResult:
    """Represents the result of a research job execution"""

    def __init__(self, user_id: str, config_name: str, job_type: str):
        self.user_id = user_id
        self.config_name = config_name
        self.job_type = job_type
        self.started_at = datetime.now().isoformat()
        self.completed_at = None
        self.success = False
        self.error_message = None
        self.results_path = None
        self.metrics = {}

    def complete(self, success: bool, results_path: str = None, error: str = None, metrics: Dict = None):
        """Mark job as completed"""
        self.completed_at = datetime.now().isoformat()
        self.success = success
        self.results_path = results_path
        self.error_message = error
        self.metrics = metrics or {}


class ResearchScheduler:
    """Manages scheduled research jobs for all users"""

    def __init__(self):
        self.config_manager = UserResearchConfigManager()
        self.running = False
        self.scheduler_thread = None
        self.active_jobs = {}
        self.job_history = []
        self.results_dir = Path(__file__).parent / "scheduled_results"
        self.results_dir.mkdir(exist_ok=True)

    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Research scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Research scheduler stopped")

    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

    def register_user_configs(self):
        """Register all user configurations with the scheduler"""
        logger.info("Registering user configurations...")

        # Clear existing scheduled jobs
        schedule.clear()

        # Find all user config files
        config_files = list(self.config_manager.config_dir.glob("*.json"))
        registered_count = 0

        for config_file in config_files:
            try:
                with open(config_file, "r") as f:
                    config_data = json.load(f)

                config = UserResearchConfig(**config_data)

                if config.auto_run_enabled and config.schedule:
                    self._schedule_config(config)
                    registered_count += 1

            except Exception as e:
                logger.error(f"Failed to register config {config_file}: {e}")

        logger.info(f"Registered {registered_count} scheduled research configurations")

    def _schedule_config(self, config: UserResearchConfig):
        """Schedule a specific user configuration"""
        try:
            schedule_obj = config.schedule
            job_func = lambda: self._execute_research_job(config)

            if schedule_obj.frequency == ResearchFrequency.DAILY:
                schedule.every().day.at(schedule_obj.time_of_day).do(job_func)

            elif schedule_obj.frequency == ResearchFrequency.WEEKLY:
                # Schedule for specific days of week
                for day_num in schedule_obj.days_of_week:
                    day_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][day_num]
                    getattr(schedule.every(), day_name).at(schedule_obj.time_of_day).do(job_func)

            elif schedule_obj.frequency == ResearchFrequency.BIWEEKLY:
                # Schedule twice a week
                schedule.every().monday.at(schedule_obj.time_of_day).do(job_func)
                schedule.every().thursday.at(schedule_obj.time_of_day).do(job_func)

            elif schedule_obj.frequency == ResearchFrequency.MONTHLY:
                # Schedule on first day of month (approximation)
                schedule.every().monday.at(schedule_obj.time_of_day).do(job_func)

            logger.info(
                f"Scheduled research job: {config.user_id}/{config.config_name} - {schedule_obj.frequency.value}"
            )

        except Exception as e:
            logger.error(f"Failed to schedule config {config.config_name}: {e}")

    def _execute_research_job(self, config: UserResearchConfig):
        """Execute a research job for a user configuration"""
        job_id = f"{config.user_id}_{config.config_name}_{int(time.time())}"

        logger.info(f"Starting research job: {job_id}")

        # Create job result tracker
        result = ResearchJobResult(config.user_id, config.config_name, "scheduled_research")
        self.active_jobs[job_id] = result

        try:
            # Execute research based on enabled sources
            results_paths = []
            metrics = {}

            # Reddit research
            if any(source.value == "reddit" for source in config.enabled_sources):
                reddit_result = asyncio.run(self._execute_reddit_research(config, job_id))
                if reddit_result:
                    results_paths.append(reddit_result["path"])
                    metrics.update(reddit_result.get("metrics", {}))

            # LinkedIn research (placeholder for future implementation)
            if any(source.value == "linkedin" for source in config.enabled_sources):
                logger.info(f"LinkedIn research scheduled for {job_id} (not yet implemented)")

            # Twitter research (placeholder for future implementation)
            if any(source.value == "twitter" for source in config.enabled_sources):
                logger.info(f"Twitter research scheduled for {job_id} (not yet implemented)")

            # Mark job as successful
            result.complete(success=True, results_path=results_paths[0] if results_paths else None, metrics=metrics)

            # Update config last run time
            self.config_manager.update_config(
                config.user_id, config.config_name, {"last_run_at": datetime.now().isoformat()}
            )

            logger.info(f"Completed research job: {job_id}")

        except Exception as e:
            logger.error(f"Research job failed: {job_id} - {e}")
            result.complete(success=False, error=str(e))

        finally:
            # Move from active to history
            self.job_history.append(result)
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]

            # Keep only last 100 job results
            if len(self.job_history) > 100:
                self.job_history = self.job_history[-100:]

    async def _execute_reddit_research(self, config: UserResearchConfig, job_id: str) -> Optional[Dict]:
        """Execute Reddit research for a configuration"""
        try:
            if not config.reddit_config:
                logger.warning(f"Reddit enabled but no Reddit config for {job_id}")
                return None

            logger.info(f"Starting Reddit research for {job_id}")

            # Create custom scraper config
            scraper_config = {
                "session_name": f"Scheduled_{config.config_name}_{job_id}",
                "search_query": " ".join(config.reddit_config.search_topics),
                "subreddits": config.reddit_config.subreddits,
                "max_posts_per_subreddit": config.reddit_config.max_posts_per_subreddit,
                "max_comments_per_post": config.reddit_config.max_comments_per_post,
            }

            # Stage 1: Raw data collection
            scraper = RawRedditScraperCLI()
            scraper.results_dir = self.results_dir / config.user_id / job_id / "raw_data"
            scraper.results_dir.mkdir(parents=True, exist_ok=True)

            await scraper.initialize_workers()
            success = await scraper.run_raw_collection_session(scraper_config)

            if not success:
                logger.error(f"Raw data collection failed for {job_id}")
                return None

            # Stage 2: AI Analysis (if comprehensive analysis is enabled)
            if config.analysis_depth.value in ["standard", "comprehensive"]:
                logger.info(f"Starting AI analysis for {job_id}")

                analyzer = RedditAIAnalyzer()
                analyzer.analyzed_data_dir = self.results_dir / config.user_id / job_id / "analyzed_data"
                analyzer.analyzed_data_dir.mkdir(parents=True, exist_ok=True)

                # Find the raw dataset
                raw_files = list(scraper.results_dir.glob("raw_reddit_dataset_*.json"))
                if raw_files:
                    raw_dataset = await analyzer.load_raw_dataset(raw_files[0])
                    if raw_dataset:
                        await analyzer.initialize_ai_client()
                        await analyzer.analyze_dataset(raw_dataset)

            # Generate summary metrics
            metrics = {
                "subreddits_processed": len(config.reddit_config.subreddits),
                "max_posts_per_subreddit": config.reddit_config.max_posts_per_subreddit,
                "analysis_depth": config.analysis_depth.value,
                "completed_at": datetime.now().isoformat(),
            }

            return {"path": str(scraper.results_dir), "metrics": metrics}

        except Exception as e:
            logger.error(f"Reddit research failed for {job_id}: {e}")
            return None

    def get_job_status(self, user_id: str = None) -> Dict:
        """Get status of active and recent jobs"""
        active = list(self.active_jobs.values())
        recent_history = self.job_history[-20:]  # Last 20 jobs

        if user_id:
            active = [job for job in active if job.user_id == user_id]
            recent_history = [job for job in recent_history if job.user_id == user_id]

        return {
            "active_jobs": len(active),
            "active_job_details": [
                {
                    "user_id": job.user_id,
                    "config_name": job.config_name,
                    "started_at": job.started_at,
                    "job_type": job.job_type,
                }
                for job in active
            ],
            "recent_jobs": [
                {
                    "user_id": job.user_id,
                    "config_name": job.config_name,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "success": job.success,
                    "error": job.error_message,
                }
                for job in recent_history
            ],
        }

    def trigger_manual_job(self, user_id: str, config_name: str) -> bool:
        """Manually trigger a research job"""
        try:
            config = self.config_manager.load_config(user_id, config_name)
            if not config:
                logger.error(f"Config not found: {user_id}/{config_name}")
                return False

            # Execute in background thread to avoid blocking
            thread = threading.Thread(target=self._execute_research_job, args=(config,), daemon=True)
            thread.start()

            logger.info(f"Manually triggered research job: {user_id}/{config_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger manual job: {e}")
            return False


def main():
    """CLI interface for the research scheduler"""
    import argparse

    parser = argparse.ArgumentParser(description="Research Scheduler")
    parser.add_argument("--start", action="store_true", help="Start the scheduler daemon")
    parser.add_argument("--status", action="store_true", help="Show scheduler status")
    parser.add_argument("--trigger", nargs=2, metavar=("USER_ID", "CONFIG_NAME"), help="Manually trigger a job")
    parser.add_argument("--register", action="store_true", help="Register all user configurations")

    args = parser.parse_args()

    scheduler = ResearchScheduler()

    if args.start:
        print("🚀 Starting Research Scheduler...")
        scheduler.register_user_configs()
        scheduler.start()

        try:
            print("✅ Scheduler running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping scheduler...")
            scheduler.stop()

    elif args.status:
        status = scheduler.get_job_status()
        print(f"📊 Scheduler Status:")
        print(f"   Active jobs: {status['active_jobs']}")
        print(f"   Recent jobs: {len(status['recent_jobs'])}")

        if status["active_job_details"]:
            print("\n🔄 Active Jobs:")
            for job in status["active_job_details"]:
                print(f"   - {job['user_id']}/{job['config_name']} (started: {job['started_at']})")

        if status["recent_jobs"]:
            print("\n📋 Recent Jobs:")
            for job in status["recent_jobs"][-5:]:  # Show last 5
                status_icon = "✅" if job["success"] else "❌"
                print(f"   {status_icon} {job['user_id']}/{job['config_name']} - {job['completed_at']}")

    elif args.trigger:
        user_id, config_name = args.trigger
        success = scheduler.trigger_manual_job(user_id, config_name)
        if success:
            print(f"✅ Triggered research job: {user_id}/{config_name}")
        else:
            print(f"❌ Failed to trigger job: {user_id}/{config_name}")

    elif args.register:
        scheduler.register_user_configs()
        print("✅ Registered all user configurations")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
