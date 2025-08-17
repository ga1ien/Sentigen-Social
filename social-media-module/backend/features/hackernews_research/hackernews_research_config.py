#!/usr/bin/env python3
"""
Hacker News Research Configuration System
Allows users to configure their HN research parameters, topics, and scheduling
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
    HACKERNEWS = "hackernews"


class AnalysisDepth(Enum):
    BASIC = "basic"  # Fast, essential insights only
    STANDARD = "standard"  # Balanced analysis
    COMPREHENSIVE = "comprehensive"  # Deep analysis, all features


class HNStoryType(Enum):
    TOP = "top"  # Top stories (most popular)
    NEW = "new"  # Newest stories
    BEST = "best"  # Best stories (highest quality)
    ASK = "ask"  # Ask HN posts (Q&A)
    SHOW = "show"  # Show HN posts (product launches)
    JOB = "job"  # Job posts


@dataclass
class HackerNewsConfig:
    """Hacker News-specific research configuration"""

    story_types: List[HNStoryType]
    search_topics: List[str]
    max_stories_per_type: int = 15
    max_comments_per_story: int = 30
    min_score: int = 10
    min_comments: int = 5
    comment_depth: int = 3  # How deep to fetch comment threads
    exclude_jobs: bool = True
    time_range_hours: int = 24  # Only stories from last N hours

    def __post_init__(self):
        # Convert string enums to enum objects if needed
        if self.story_types and isinstance(self.story_types[0], str):
            self.story_types = [HNStoryType(t) for t in self.story_types]


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
        # Convert string enum to enum object if needed
        if isinstance(self.frequency, str):
            self.frequency = ResearchFrequency(self.frequency)


@dataclass
class HackerNewsResearchConfig:
    """Complete Hacker News research configuration"""

    user_id: str
    workspace_id: str
    config_name: str
    description: str

    # Hacker News configuration (required)
    hackernews_config: HackerNewsConfig

    # Analysis settings
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    ai_model: str = "gpt-5-mini"
    focus_areas: List[str] = None  # business_intelligence, competitive_analysis, trend_analysis

    # Scheduling
    schedule: Optional[ResearchSchedule] = None
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
        # Convert string enums to enum objects if needed
        if isinstance(self.analysis_depth, str):
            self.analysis_depth = AnalysisDepth(self.analysis_depth)


class HackerNewsResearchConfigManager:
    """Manages Hacker News research configurations"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = Path(__file__).parent / "user_configs"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def create_config(self, config: HackerNewsResearchConfig) -> bool:
        """Create a new HN research configuration"""
        try:
            config.created_at = datetime.now().isoformat()
            config.updated_at = config.created_at

            filepath = self.config_dir / f"{config.user_id}_{config.config_name}.json"

            with open(filepath, "w") as f:
                json.dump(asdict(config), f, indent=2, default=str)

            print(f"✅ Created HN research config: {config.config_name}")
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

    def load_config(self, user_id: str, config_name: str) -> Optional[HackerNewsResearchConfig]:
        """Load a HN research configuration"""
        try:
            filepath = self.config_dir / f"{user_id}_{config_name}.json"

            if not filepath.exists():
                print(f"❌ Config not found: {config_name}")
                return None

            with open(filepath, "r") as f:
                data = json.load(f)

            # Convert back to dataclass
            config = HackerNewsResearchConfig(**data)
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
        """Delete a HN research configuration"""
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
    """Create sample HN research configurations for different use cases"""

    manager = HackerNewsResearchConfigManager()

    # Sample 1: Tech Trends Research
    tech_trends_config = HackerNewsResearchConfig(
        user_id="user_001",
        workspace_id="workspace_001",
        config_name="tech_trends",
        description="Daily HN research on technology trends and innovations",
        hackernews_config=HackerNewsConfig(
            story_types=[HNStoryType.TOP, HNStoryType.BEST],
            search_topics=["AI", "machine learning", "startup", "technology", "programming"],
            max_stories_per_type=12,
            max_comments_per_story=25,
            min_score=50,
            min_comments=10,
            comment_depth=2,
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(frequency=ResearchFrequency.DAILY, time_of_day="08:00", timezone="America/New_York"),
        auto_run_enabled=True,
        focus_areas=["business_intelligence", "trend_analysis", "technology_insights"],
        generate_content_ideas=True,
    )

    # Sample 2: Ask HN Q&A Research
    ask_hn_config = HackerNewsResearchConfig(
        user_id="user_001",
        workspace_id="workspace_001",
        config_name="ask_hn_insights",
        description="Weekly Ask HN research for community insights and Q&A content",
        hackernews_config=HackerNewsConfig(
            story_types=[HNStoryType.ASK],
            search_topics=["career", "startup advice", "technical questions", "business"],
            max_stories_per_type=20,
            max_comments_per_story=40,
            min_score=20,
            min_comments=15,
            comment_depth=3,
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(
            frequency=ResearchFrequency.WEEKLY, time_of_day="09:00", days_of_week=[0]  # Monday only
        ),
        auto_run_enabled=True,
        focus_areas=["community_insights", "career_advice", "business_strategy"],
    )

    # Sample 3: Show HN Product Launches
    show_hn_config = HackerNewsResearchConfig(
        user_id="user_002",
        workspace_id="workspace_002",
        config_name="product_launches",
        description="Bi-weekly Show HN research for new product launches and innovations",
        hackernews_config=HackerNewsConfig(
            story_types=[HNStoryType.SHOW],
            search_topics=["product launch", "new tool", "open source", "SaaS"],
            max_stories_per_type=15,
            max_comments_per_story=30,
            min_score=30,
            min_comments=8,
            comment_depth=2,
        ),
        analysis_depth=AnalysisDepth.STANDARD,
        schedule=ResearchSchedule(
            frequency=ResearchFrequency.BIWEEKLY, time_of_day="10:00", days_of_week=[1, 4]  # Tuesday and Friday
        ),
        auto_run_enabled=True,
        focus_areas=["product_intelligence", "market_opportunities", "innovation_trends"],
        generate_content_ideas=True,
        export_formats=["json", "markdown", "csv"],
    )

    # Sample 4: Comprehensive Tech Intelligence
    comprehensive_config = HackerNewsResearchConfig(
        user_id="user_003",
        workspace_id="workspace_003",
        config_name="comprehensive_tech_intel",
        description="Comprehensive HN research across all story types for complete tech intelligence",
        hackernews_config=HackerNewsConfig(
            story_types=[HNStoryType.TOP, HNStoryType.ASK, HNStoryType.SHOW, HNStoryType.BEST],
            search_topics=["artificial intelligence", "blockchain", "cybersecurity", "cloud computing", "devops"],
            max_stories_per_type=10,
            max_comments_per_story=35,
            min_score=40,
            min_comments=12,
            comment_depth=3,
            time_range_hours=48,  # Last 48 hours
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(
            frequency=ResearchFrequency.WEEKLY, time_of_day="07:00", days_of_week=[0, 3]  # Monday and Thursday
        ),
        auto_run_enabled=True,
        focus_areas=["business_intelligence", "competitive_analysis", "trend_analysis", "technology_insights"],
        generate_content_ideas=True,
        generate_insights=True,
        export_formats=["json", "markdown", "pdf"],
    )

    # Save sample configs
    configs = [tech_trends_config, ask_hn_config, show_hn_config, comprehensive_config]
    for config in configs:
        manager.create_config(config)

    print(f"✅ Created {len(configs)} sample HN configurations")
    return configs


def main():
    """CLI interface for managing HN research configurations"""
    import argparse

    parser = argparse.ArgumentParser(description="Hacker News Research Configuration Manager")
    parser.add_argument("--create-samples", action="store_true", help="Create sample configurations")
    parser.add_argument("--list", help="List configurations for user ID")
    parser.add_argument("--show", nargs=2, metavar=("USER_ID", "CONFIG_NAME"), help="Show specific configuration")

    args = parser.parse_args()

    if args.create_samples:
        create_sample_configs()
    elif args.list:
        manager = HackerNewsResearchConfigManager()
        configs = manager.list_user_configs(args.list)
        print(f"HN Configurations for user {args.list}:")
        for config in configs:
            print(f"  - {config}")
    elif args.show:
        user_id, config_name = args.show
        manager = HackerNewsResearchConfigManager()
        config = manager.load_config(user_id, config_name)
        if config:
            print(json.dumps(asdict(config), indent=2, default=str))


if __name__ == "__main__":
    main()
