#!/usr/bin/env python3
"""
User Research Configuration System
Allows users to configure their research parameters, topics, and scheduling
"""

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


class ResearchFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ContentSource(Enum):
    REDDIT = "reddit"


class AnalysisDepth(Enum):
    BASIC = "basic"  # Fast, essential insights only
    STANDARD = "standard"  # Balanced analysis
    COMPREHENSIVE = "comprehensive"  # Deep analysis, all features


@dataclass
class RedditConfig:
    """Reddit-specific research configuration"""

    subreddits: List[str]
    search_topics: List[str]
    max_posts_per_subreddit: int = 10
    max_comments_per_post: int = 25
    sort_by: str = "hot"  # hot, new, top, rising
    time_filter: str = "week"  # hour, day, week, month, year, all
    min_score: int = 10
    exclude_nsfw: bool = True
    include_stickied: bool = False


@dataclass
class LinkedInConfig:
    """LinkedIn-specific research configuration"""

    search_topics: List[str]
    company_pages: List[str]
    industry_hashtags: List[str]
    max_posts_per_topic: int = 15
    include_comments: bool = True
    max_comments_per_post: int = 20
    post_types: List[str] = None  # article, video, image, poll

    def __post_init__(self):
        if self.post_types is None:
            self.post_types = ["article", "video", "image"]


@dataclass
class TwitterConfig:
    """Twitter-specific research configuration"""

    search_topics: List[str]
    hashtags: List[str]
    accounts_to_monitor: List[str]
    max_tweets_per_topic: int = 50
    include_replies: bool = True
    include_retweets: bool = False
    min_engagement: int = 5  # minimum likes/retweets


@dataclass
class ResearchSchedule:
    """Research scheduling configuration"""

    frequency: ResearchFrequency
    time_of_day: str = "09:00"  # HH:MM format
    timezone: str = "UTC"
    days_of_week: List[int] = None  # 0=Monday, 6=Sunday, None=all days
    custom_cron: Optional[str] = None  # For custom scheduling

    def __post_init__(self):
        if self.days_of_week is None:
            self.days_of_week = list(range(7))  # All days


@dataclass
class RedditResearchConfig:
    """Reddit-specific research configuration"""

    user_id: str
    workspace_id: str
    config_name: str
    description: str

    # Reddit configuration (required)
    reddit_config: RedditConfig

    # Analysis settings
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    ai_model: str = "gpt-5-mini"
    focus_areas: List[str] = None  # business_intelligence, competitive_analysis, trend_analysis

    # Scheduling
    schedule: ResearchSchedule = None
    auto_run_enabled: bool = False

    # Output preferences
    generate_summary: bool = True
    generate_insights: bool = True
    generate_content_ideas: bool = True
    export_formats: List[str] = None  # json, csv, pdf, markdown

    # Metadata
    created_at: str = None
    updated_at: str = None
    last_run_at: Optional[str] = None

    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = ["business_intelligence", "trend_analysis"]
        if self.export_formats is None:
            self.export_formats = ["json", "markdown"]
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


class RedditResearchConfigManager:
    """Manages Reddit research configurations"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = Path(__file__).parent / "user_configs"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def create_config(self, config: RedditResearchConfig) -> bool:
        """Create a new user research configuration"""
        try:
            config.created_at = datetime.now().isoformat()
            config.updated_at = config.created_at

            filepath = self.config_dir / f"{config.user_id}_{config.config_name}.json"

            with open(filepath, "w") as f:
                json.dump(asdict(config), f, indent=2, default=str)

            print(f"✅ Created research config: {config.config_name}")
            return True

        except Exception as e:
            print(f"❌ Failed to create config: {e}")
            return False

    def update_config(self, user_id: str, config_name: str, updates: Dict) -> bool:
        """Update an existing configuration"""
        try:
            config = self.load_config(user_id, config_name)
            if not config:
                return False

            # Update fields
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            config.updated_at = datetime.now().isoformat()

            return self.create_config(config)  # Save updated config

        except Exception as e:
            print(f"❌ Failed to update config: {e}")
            return False

    def load_config(self, user_id: str, config_name: str) -> Optional[RedditResearchConfig]:
        """Load a user research configuration"""
        try:
            filepath = self.config_dir / f"{user_id}_{config_name}.json"

            if not filepath.exists():
                print(f"❌ Config not found: {config_name}")
                return None

            with open(filepath, "r") as f:
                data = json.load(f)

            # Convert back to dataclass
            config = RedditResearchConfig(**data)
            return config

        except Exception as e:
            print(f"❌ Failed to load config: {e}")
            return None

    def list_user_configs(self, user_id: str) -> List[str]:
        """List all configurations for a user"""
        try:
            pattern = f"{user_id}_*.json"
            config_files = list(self.config_dir.glob(pattern))

            config_names = []
            for filepath in config_files:
                # Extract config name from filename
                filename = filepath.stem
                config_name = filename.replace(f"{user_id}_", "")
                config_names.append(config_name)

            return config_names

        except Exception as e:
            print(f"❌ Failed to list configs: {e}")
            return []

    def delete_config(self, user_id: str, config_name: str) -> bool:
        """Delete a user research configuration"""
        try:
            filepath = self.config_dir / f"{user_id}_{config_name}.json"

            if filepath.exists():
                filepath.unlink()
                print(f"✅ Deleted config: {config_name}")
                return True
            else:
                print(f"❌ Config not found: {config_name}")
                return False

        except Exception as e:
            print(f"❌ Failed to delete config: {e}")
            return False


def create_sample_configs():
    """Create sample Reddit research configurations for different use cases"""

    manager = RedditResearchConfigManager()

    # Sample 1: AI Business Tools Research
    ai_tools_config = RedditResearchConfig(
        user_id="user_001",
        workspace_id="workspace_001",
        config_name="ai_business_tools",
        description="Daily Reddit research on AI automation and business productivity tools",
        reddit_config=RedditConfig(
            subreddits=["artificial", "productivity", "Entrepreneur", "SaaS", "MachineLearning"],
            search_topics=["AI automation", "business tools", "productivity software", "workflow automation"],
            max_posts_per_subreddit=8,
            max_comments_per_post=30,
            min_score=20,
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(frequency=ResearchFrequency.DAILY, time_of_day="08:00", timezone="America/New_York"),
        auto_run_enabled=True,
        focus_areas=["business_intelligence", "competitive_analysis", "trend_analysis"],
        generate_content_ideas=True,
    )

    # Sample 2: Weekly Competitive Intelligence
    competitive_config = RedditResearchConfig(
        user_id="user_001",
        workspace_id="workspace_001",
        config_name="competitive_intelligence",
        description="Weekly Reddit deep dive into competitor activities and market trends",
        reddit_config=RedditConfig(
            subreddits=["startups", "Entrepreneur", "SaaS", "business", "venturecapital"],
            search_topics=["competitor analysis", "market research", "business strategy", "startup funding"],
            max_posts_per_subreddit=15,
            max_comments_per_post=50,
            sort_by="top",
            time_filter="week",
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(
            frequency=ResearchFrequency.WEEKLY, time_of_day="09:00", days_of_week=[0]  # Monday only
        ),
        auto_run_enabled=True,
        focus_areas=["competitive_analysis", "market_intelligence", "business_strategy"],
    )

    # Sample 3: Content Ideas Generation
    content_ideas_config = RedditResearchConfig(
        user_id="user_002",
        workspace_id="workspace_002",
        config_name="content_inspiration",
        description="Bi-weekly Reddit research for content ideas and trending topics",
        reddit_config=RedditConfig(
            subreddits=["marketing", "socialmedia", "content", "copywriting", "digitalmarketing"],
            search_topics=["content marketing", "social media strategy", "viral content", "engagement tips"],
            max_posts_per_subreddit=12,
            max_comments_per_post=25,
        ),
        analysis_depth=AnalysisDepth.STANDARD,
        schedule=ResearchSchedule(
            frequency=ResearchFrequency.BIWEEKLY, time_of_day="10:00", days_of_week=[0, 3]  # Monday and Thursday
        ),
        auto_run_enabled=True,
        focus_areas=["trend_analysis", "content_opportunities"],
        generate_content_ideas=True,
        export_formats=["json", "markdown", "csv"],
    )

    # Save sample configs
    configs = [ai_tools_config, competitive_config, content_ideas_config]
    for config in configs:
        manager.create_config(config)

    print(f"✅ Created {len(configs)} sample configurations")
    return configs


def main():
    """CLI interface for managing research configurations"""
    import argparse

    parser = argparse.ArgumentParser(description="User Research Configuration Manager")
    parser.add_argument("--create-samples", action="store_true", help="Create sample configurations")
    parser.add_argument("--list", help="List configurations for user ID")
    parser.add_argument("--show", nargs=2, metavar=("USER_ID", "CONFIG_NAME"), help="Show specific configuration")

    args = parser.parse_args()

    if args.create_samples:
        create_sample_configs()
    elif args.list:
        manager = UserResearchConfigManager()
        configs = manager.list_user_configs(args.list)
        print(f"Configurations for user {args.list}:")
        for config in configs:
            print(f"  - {config}")
    elif args.show:
        user_id, config_name = args.show
        manager = UserResearchConfigManager()
        config = manager.load_config(user_id, config_name)
        if config:
            print(json.dumps(asdict(config), indent=2, default=str))


if __name__ == "__main__":
    main()
