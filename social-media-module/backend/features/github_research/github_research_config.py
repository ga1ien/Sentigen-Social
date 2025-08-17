#!/usr/bin/env python3
"""
GitHub Research Configuration System
Allows users to configure their GitHub research parameters, topics, and scheduling
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
    GITHUB = "github"


class AnalysisDepth(Enum):
    BASIC = "basic"  # Fast, essential insights only
    STANDARD = "standard"  # Balanced analysis
    COMPREHENSIVE = "comprehensive"  # Deep analysis, all features


class GitHubContentType(Enum):
    TRENDING_REPOS = "trending_repos"
    VIRAL_REPOS = "viral_repos"
    NEW_RELEASES = "new_releases"
    ISSUES = "issues"
    DISCUSSIONS = "discussions"
    PULL_REQUESTS = "pull_requests"
    README_FILES = "readme_files"
    COMMIT_ACTIVITY = "commit_activity"


class GitHubTimeRange(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class GitHubConfig:
    """GitHub-specific research configuration"""

    content_types: List[GitHubContentType]
    search_topics: List[str]
    languages: List[str] = None  # Programming languages to focus on
    max_repos_per_search: int = 20
    min_stars: int = 100
    min_forks: int = 10
    time_range: GitHubTimeRange = GitHubTimeRange.WEEKLY
    include_readme: bool = True
    include_issues: bool = True
    include_discussions: bool = True
    max_issues_per_repo: int = 10
    viral_threshold_stars_per_day: int = 50
    exclude_archived: bool = True
    exclude_forks: bool = True

    def __post_init__(self):
        # Convert string enums to enum objects if needed
        if self.content_types and isinstance(self.content_types[0], str):
            self.content_types = [GitHubContentType(t) for t in self.content_types]
        if isinstance(self.time_range, str):
            self.time_range = GitHubTimeRange(self.time_range)
        if self.languages is None:
            self.languages = []


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
class GitHubResearchConfig:
    """Complete GitHub research configuration"""

    user_id: str
    workspace_id: str
    config_name: str
    description: str

    # GitHub configuration (required)
    github_config: GitHubConfig

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
            self.focus_areas = ["business_intelligence", "trend_analysis", "technology_insights"]
        if self.export_formats is None:
            self.export_formats = ["json", "markdown"]
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
        # Convert string enums to enum objects if needed
        if isinstance(self.analysis_depth, str):
            self.analysis_depth = AnalysisDepth(self.analysis_depth)


class GitHubResearchConfigManager:
    """Manages GitHub research configurations"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = Path(__file__).parent / "user_configs"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def create_config(self, config: GitHubResearchConfig) -> bool:
        """Create a new GitHub research configuration"""
        try:
            config.created_at = datetime.now().isoformat()
            config.updated_at = config.created_at

            filepath = self.config_dir / f"{config.user_id}_{config.config_name}.json"

            with open(filepath, "w") as f:
                json.dump(asdict(config), f, indent=2, default=str)

            print(f"✅ Created GitHub research config: {config.config_name}")
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

    def load_config(self, user_id: str, config_name: str) -> Optional[GitHubResearchConfig]:
        """Load a GitHub research configuration"""
        try:
            filepath = self.config_dir / f"{user_id}_{config_name}.json"

            if not filepath.exists():
                print(f"❌ Config not found: {config_name}")
                return None

            with open(filepath, "r") as f:
                data = json.load(f)

            # Convert back to dataclass
            config = GitHubResearchConfig(**data)
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
        """Delete a GitHub research configuration"""
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
    """Create sample GitHub research configurations for different use cases"""

    manager = GitHubResearchConfigManager()

    # Sample 1: Trending Tech Research
    trending_tech_config = GitHubResearchConfig(
        user_id="user_001",
        workspace_id="workspace_001",
        config_name="trending_tech",
        description="Daily GitHub research on trending technologies and viral repos",
        github_config=GitHubConfig(
            content_types=[GitHubContentType.TRENDING_REPOS, GitHubContentType.VIRAL_REPOS],
            search_topics=["AI", "machine learning", "web development", "blockchain", "devops"],
            languages=["Python", "JavaScript", "TypeScript", "Rust", "Go"],
            max_repos_per_search=15,
            min_stars=500,
            min_forks=50,
            time_range=GitHubTimeRange.WEEKLY,
            viral_threshold_stars_per_day=100,
            include_readme=True,
            include_issues=True,
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(frequency=ResearchFrequency.DAILY, time_of_day="08:00", timezone="America/New_York"),
        auto_run_enabled=True,
        focus_areas=["technology_insights", "trend_analysis", "innovation_tracking"],
        generate_content_ideas=True,
    )

    # Sample 2: Developer Tools Intelligence
    dev_tools_config = GitHubResearchConfig(
        user_id="user_001",
        workspace_id="workspace_001",
        config_name="dev_tools_intel",
        description="Weekly research on developer tools, frameworks, and productivity solutions",
        github_config=GitHubConfig(
            content_types=[GitHubContentType.TRENDING_REPOS, GitHubContentType.NEW_RELEASES, GitHubContentType.ISSUES],
            search_topics=["developer tools", "framework", "productivity", "CLI", "IDE", "testing"],
            languages=["JavaScript", "Python", "Go", "Rust", "TypeScript"],
            max_repos_per_search=20,
            min_stars=1000,
            min_forks=100,
            time_range=GitHubTimeRange.MONTHLY,
            include_readme=True,
            include_issues=True,
            max_issues_per_repo=15,
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(
            frequency=ResearchFrequency.WEEKLY, time_of_day="09:00", days_of_week=[0]  # Monday only
        ),
        auto_run_enabled=True,
        focus_areas=["competitive_analysis", "market_intelligence", "developer_experience"],
    )

    # Sample 3: Open Source Project Monitoring
    opensource_config = GitHubResearchConfig(
        user_id="user_002",
        workspace_id="workspace_002",
        config_name="opensource_monitoring",
        description="Monitor open source projects for community insights and contribution opportunities",
        github_config=GitHubConfig(
            content_types=[GitHubContentType.ISSUES, GitHubContentType.DISCUSSIONS, GitHubContentType.PULL_REQUESTS],
            search_topics=["open source", "community", "contribution", "maintainer"],
            languages=["Python", "JavaScript", "Java", "C++"],
            max_repos_per_search=25,
            min_stars=2000,
            min_forks=200,
            time_range=GitHubTimeRange.WEEKLY,
            include_readme=True,
            include_issues=True,
            include_discussions=True,
            max_issues_per_repo=20,
        ),
        analysis_depth=AnalysisDepth.STANDARD,
        schedule=ResearchSchedule(
            frequency=ResearchFrequency.BIWEEKLY, time_of_day="10:00", days_of_week=[1, 4]  # Tuesday and Friday
        ),
        auto_run_enabled=True,
        focus_areas=["community_insights", "contribution_opportunities", "maintainer_challenges"],
        generate_content_ideas=True,
        export_formats=["json", "markdown", "csv"],
    )

    # Sample 4: Startup Tech Stack Analysis
    startup_tech_config = GitHubResearchConfig(
        user_id="user_003",
        workspace_id="workspace_003",
        config_name="startup_tech_stacks",
        description="Analyze trending technologies and tools used by startups and growing companies",
        github_config=GitHubConfig(
            content_types=[
                GitHubContentType.TRENDING_REPOS,
                GitHubContentType.VIRAL_REPOS,
                GitHubContentType.NEW_RELEASES,
            ],
            search_topics=["startup", "SaaS", "microservices", "cloud native", "scalability"],
            languages=["JavaScript", "Python", "Go", "Rust", "TypeScript", "Kotlin"],
            max_repos_per_search=18,
            min_stars=800,
            min_forks=80,
            time_range=GitHubTimeRange.WEEKLY,
            viral_threshold_stars_per_day=75,
            include_readme=True,
            include_issues=False,  # Focus on tech, not problems
            exclude_archived=True,
            exclude_forks=True,
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(
            frequency=ResearchFrequency.WEEKLY, time_of_day="07:00", days_of_week=[0, 3]  # Monday and Thursday
        ),
        auto_run_enabled=True,
        focus_areas=["business_intelligence", "technology_adoption", "startup_ecosystem", "scalability_patterns"],
        generate_content_ideas=True,
        generate_insights=True,
        export_formats=["json", "markdown", "pdf"],
    )

    # Sample 5: AI/ML Research Focus
    ai_ml_config = GitHubResearchConfig(
        user_id="user_004",
        workspace_id="workspace_004",
        config_name="ai_ml_research",
        description="Deep dive into AI/ML repositories, models, and research implementations",
        github_config=GitHubConfig(
            content_types=[
                GitHubContentType.TRENDING_REPOS,
                GitHubContentType.VIRAL_REPOS,
                GitHubContentType.README_FILES,
            ],
            search_topics=[
                "artificial intelligence",
                "machine learning",
                "deep learning",
                "LLM",
                "neural network",
                "computer vision",
            ],
            languages=["Python", "Jupyter Notebook", "R", "C++", "CUDA"],
            max_repos_per_search=12,
            min_stars=1500,
            min_forks=150,
            time_range=GitHubTimeRange.WEEKLY,
            viral_threshold_stars_per_day=200,  # Higher threshold for AI repos
            include_readme=True,
            include_issues=True,
            max_issues_per_repo=8,
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(frequency=ResearchFrequency.DAILY, time_of_day="06:00", timezone="UTC"),
        auto_run_enabled=True,
        focus_areas=["research_trends", "model_innovations", "implementation_patterns", "academic_industry_bridge"],
        generate_content_ideas=True,
        export_formats=["json", "markdown"],
    )

    # Save sample configs
    configs = [trending_tech_config, dev_tools_config, opensource_config, startup_tech_config, ai_ml_config]
    for config in configs:
        manager.create_config(config)

    print(f"✅ Created {len(configs)} sample GitHub configurations")
    return configs


def main():
    """CLI interface for managing GitHub research configurations"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Research Configuration Manager")
    parser.add_argument("--create-samples", action="store_true", help="Create sample configurations")
    parser.add_argument("--list", help="List configurations for user ID")
    parser.add_argument("--show", nargs=2, metavar=("USER_ID", "CONFIG_NAME"), help="Show specific configuration")

    args = parser.parse_args()

    if args.create_samples:
        create_sample_configs()
    elif args.list:
        manager = GitHubResearchConfigManager()
        configs = manager.list_user_configs(args.list)
        print(f"GitHub Configurations for user {args.list}:")
        for config in configs:
            print(f"  - {config}")
    elif args.show:
        user_id, config_name = args.show
        manager = GitHubResearchConfigManager()
        config = manager.load_config(user_id, config_name)
        if config:
            print(json.dumps(asdict(config), indent=2, default=str))


if __name__ == "__main__":
    main()
