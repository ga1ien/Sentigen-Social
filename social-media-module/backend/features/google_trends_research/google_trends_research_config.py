#!/usr/bin/env python3
"""
Google Trends Research Configuration System
Manages user-configurable parameters for Google Trends research
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TrendsTimeframe(Enum):
    """Available timeframes for Google Trends analysis"""

    REALTIME = "now 1-H"
    LAST_4_HOURS = "now 4-H"
    LAST_DAY = "now 1-d"
    LAST_7_DAYS = "now 7-d"
    LAST_30_DAYS = "today 1-m"
    LAST_90_DAYS = "today 3-m"
    LAST_12_MONTHS = "today 12-m"
    LAST_5_YEARS = "today 5-y"
    ALL_TIME = "all"


class TrendsCategory(Enum):
    """Google Trends categories"""

    ALL = "0"
    ARTS_ENTERTAINMENT = "3"
    AUTOS_VEHICLES = "47"
    BEAUTY_FITNESS = "44"
    BOOKS_LITERATURE = "22"
    BUSINESS_INDUSTRIAL = "12"
    COMPUTERS_ELECTRONICS = "5"
    FINANCE = "7"
    FOOD_DRINK = "71"
    GAMES = "8"
    HEALTH = "45"
    HOBBIES_LEISURE = "65"
    HOME_GARDEN = "11"
    INTERNET_TELECOM = "13"
    JOBS_EDUCATION = "958"
    LAW_GOVERNMENT = "19"
    NEWS = "16"
    ONLINE_COMMUNITIES = "299"
    PEOPLE_SOCIETY = "14"
    PETS_ANIMALS = "66"
    REAL_ESTATE = "29"
    REFERENCE = "533"
    SCIENCE = "174"
    SHOPPING = "18"
    SPORTS = "20"
    TRAVEL = "67"


class TrendsGeoLocation(Enum):
    """Popular geo locations for trends analysis"""

    WORLDWIDE = ""
    UNITED_STATES = "US"
    UNITED_KINGDOM = "GB"
    CANADA = "CA"
    AUSTRALIA = "AU"
    GERMANY = "DE"
    FRANCE = "FR"
    JAPAN = "JP"
    INDIA = "IN"
    BRAZIL = "BR"


class ContentOpportunityType(Enum):
    """Types of content opportunities to discover"""

    BREAKOUT_TOPICS = "breakout"
    RISING_SEARCHES = "rising"
    QUESTION_QUERIES = "questions"
    COMPARISON_TOPICS = "comparisons"
    SEASONAL_CONTENT = "seasonal"
    VIDEO_OPPORTUNITIES = "video"
    NEWS_JACKING = "news"


class AnalysisDepth(Enum):
    """Depth of analysis to perform"""

    QUICK = "quick"  # Basic trends only
    STANDARD = "standard"  # Trends + related queries
    COMPREHENSIVE = "comprehensive"  # Full analysis with breakouts, seasonality, etc.


@dataclass
class GoogleTrendsConfig:
    """Google Trends specific research configuration"""

    # Core search parameters
    keywords: List[str] = None
    timeframe: TrendsTimeframe = TrendsTimeframe.LAST_7_DAYS
    geo_location: TrendsGeoLocation = TrendsGeoLocation.UNITED_STATES
    category: TrendsCategory = TrendsCategory.ALL

    # Content discovery settings
    opportunity_types: List[ContentOpportunityType] = None
    max_related_queries: int = 20
    breakout_threshold: int = 5000  # % growth for breakout detection
    rising_threshold: int = 100  # % growth for rising detection

    # Analysis settings
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    include_youtube_trends: bool = True
    include_news_trends: bool = True
    include_image_trends: bool = False

    # Comparison settings
    enable_keyword_comparison: bool = True
    max_comparison_keywords: int = 5

    # Geographic analysis
    include_regional_data: bool = True
    top_regions_count: int = 10

    # Seasonal analysis
    enable_seasonal_analysis: bool = False
    seasonal_lookback_years: int = 2

    # Content generation hints
    target_content_types: List[str] = None  # blog, video, social, newsletter
    target_audience: str = "general"
    content_urgency_level: str = "normal"  # low, normal, high, immediate

    # Rate limiting
    request_delay_seconds: float = 1.0
    batch_size: int = 5

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.opportunity_types is None:
            self.opportunity_types = [
                ContentOpportunityType.BREAKOUT_TOPICS,
                ContentOpportunityType.RISING_SEARCHES,
                ContentOpportunityType.QUESTION_QUERIES,
            ]
        if self.target_content_types is None:
            self.target_content_types = ["blog", "social"]


@dataclass
class ResearchSchedule:
    """Scheduling configuration for automated research"""

    frequency: str = "manual"  # manual, hourly, daily, weekly, monthly
    time_of_day: str = "09:00"
    days_of_week: List[int] = None  # 0=Monday, 6=Sunday
    timezone: str = "America/New_York"

    def __post_init__(self):
        if self.days_of_week is None:
            self.days_of_week = [0, 2, 4]  # Mon, Wed, Fri


@dataclass
class GoogleTrendsResearchConfig:
    """Complete Google Trends research configuration"""

    user_id: str
    workspace_id: str
    config_name: str
    description: str

    # Google Trends configuration (required)
    trends_config: GoogleTrendsConfig

    # Analysis settings
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    ai_model: str = "gpt-5-mini"
    focus_areas: List[str] = None  # trend_analysis, content_opportunities, competitive_intelligence

    # Scheduling
    schedule: ResearchSchedule = None
    auto_run_enabled: bool = False

    # Output settings
    generate_content_ideas: bool = True
    export_formats: List[str] = None  # json, csv, markdown

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_run_at: Optional[str] = None

    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = ["trend_analysis", "content_opportunities"]
        if self.export_formats is None:
            self.export_formats = ["json", "markdown"]
        if self.schedule is None:
            self.schedule = ResearchSchedule()
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class GoogleTrendsResearchConfigManager:
    """Manager for Google Trends research configurations"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "user_configs")

        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)

    def create_config(self, config: GoogleTrendsResearchConfig) -> str:
        """Create a new configuration"""
        config.created_at = datetime.now().isoformat()
        config.updated_at = config.created_at

        filename = f"{config.user_id}_{config.config_name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.config_dir, filename)

        with open(filepath, "w") as f:
            json.dump(asdict(config), f, indent=2, default=str)

        return filepath

    def load_config(self, user_id: str, config_name: str) -> Optional[GoogleTrendsResearchConfig]:
        """Load a configuration"""
        filename = f"{user_id}_{config_name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.config_dir, filename)

        if not os.path.exists(filepath):
            return None

        with open(filepath, "r") as f:
            data = json.load(f)

        # Convert nested dictionaries back to dataclasses
        if "trends_config" in data:
            data["trends_config"] = GoogleTrendsConfig(**data["trends_config"])
        if "schedule" in data:
            data["schedule"] = ResearchSchedule(**data["schedule"])

        return GoogleTrendsResearchConfig(**data)

    def update_config(self, config: GoogleTrendsResearchConfig) -> str:
        """Update an existing configuration"""
        config.updated_at = datetime.now().isoformat()

        filename = f"{config.user_id}_{config.config_name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.config_dir, filename)

        with open(filepath, "w") as f:
            json.dump(asdict(config), f, indent=2, default=str)

        return filepath

    def list_configs(self, user_id: str) -> List[str]:
        """List all configurations for a user"""
        configs = []
        for filename in os.listdir(self.config_dir):
            if filename.startswith(f"{user_id}_") and filename.endswith(".json"):
                config_name = filename[len(f"{user_id}_") : -5].replace("_", " ").title()
                configs.append(config_name)
        return configs

    def delete_config(self, user_id: str, config_name: str) -> bool:
        """Delete a configuration"""
        filename = f"{user_id}_{config_name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.config_dir, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False


def create_sample_configs():
    """Create sample Google Trends research configurations for different use cases"""
    manager = GoogleTrendsResearchConfigManager()

    # Sample 1: Tech Trends Monitoring
    tech_trends_config = GoogleTrendsResearchConfig(
        user_id="user_001",
        workspace_id="workspace_001",
        config_name="tech_trends_monitoring",
        description="Real-time monitoring of technology trends and breakout topics",
        trends_config=GoogleTrendsConfig(
            keywords=["AI", "ChatGPT", "machine learning", "blockchain", "cybersecurity", "cloud computing"],
            timeframe=TrendsTimeframe.LAST_DAY,
            geo_location=TrendsGeoLocation.UNITED_STATES,
            category=TrendsCategory.COMPUTERS_ELECTRONICS,
            opportunity_types=[
                ContentOpportunityType.BREAKOUT_TOPICS,
                ContentOpportunityType.RISING_SEARCHES,
                ContentOpportunityType.NEWS_JACKING,
            ],
            analysis_depth=AnalysisDepth.COMPREHENSIVE,
            include_youtube_trends=True,
            include_news_trends=True,
            target_content_types=["blog", "video", "social", "newsletter"],
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(frequency="daily", time_of_day="08:00", timezone="America/New_York"),
        auto_run_enabled=True,
        focus_areas=["trend_analysis", "content_opportunities", "competitive_intelligence"],
        generate_content_ideas=True,
    )

    # Sample 2: Content Opportunity Discovery
    content_discovery_config = GoogleTrendsResearchConfig(
        user_id="user_001",
        workspace_id="workspace_001",
        config_name="content_opportunity_discovery",
        description="Discover viral content opportunities and question-based searches",
        trends_config=GoogleTrendsConfig(
            keywords=["productivity", "remote work", "entrepreneurship", "side hustle", "passive income"],
            timeframe=TrendsTimeframe.LAST_7_DAYS,
            geo_location=TrendsGeoLocation.UNITED_STATES,
            category=TrendsCategory.BUSINESS_INDUSTRIAL,
            opportunity_types=[
                ContentOpportunityType.BREAKOUT_TOPICS,
                ContentOpportunityType.QUESTION_QUERIES,
                ContentOpportunityType.VIDEO_OPPORTUNITIES,
                ContentOpportunityType.COMPARISON_TOPICS,
            ],
            analysis_depth=AnalysisDepth.COMPREHENSIVE,
            breakout_threshold=1000,  # Lower threshold for more opportunities
            rising_threshold=50,
            max_related_queries=30,
            target_content_types=["blog", "video", "social"],
            target_audience="entrepreneurs",
            content_urgency_level="high",
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(frequency="daily", time_of_day="10:00", days_of_week=[0, 2, 4]),  # Mon, Wed, Fri
        auto_run_enabled=True,
        focus_areas=["content_opportunities", "trend_analysis"],
        generate_content_ideas=True,
        export_formats=["json", "markdown", "csv"],
    )

    # Sample 3: Seasonal Content Planning
    seasonal_planning_config = GoogleTrendsResearchConfig(
        user_id="user_002",
        workspace_id="workspace_002",
        config_name="seasonal_content_planning",
        description="Long-term seasonal content planning and trend prediction",
        trends_config=GoogleTrendsConfig(
            keywords=["fitness", "diet", "workout", "healthy recipes", "weight loss", "gym"],
            timeframe=TrendsTimeframe.LAST_12_MONTHS,
            geo_location=TrendsGeoLocation.UNITED_STATES,
            category=TrendsCategory.BEAUTY_FITNESS,
            opportunity_types=[
                ContentOpportunityType.SEASONAL_CONTENT,
                ContentOpportunityType.QUESTION_QUERIES,
                ContentOpportunityType.VIDEO_OPPORTUNITIES,
            ],
            analysis_depth=AnalysisDepth.COMPREHENSIVE,
            enable_seasonal_analysis=True,
            seasonal_lookback_years=3,
            include_regional_data=True,
            target_content_types=["blog", "video", "social"],
            target_audience="fitness enthusiasts",
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(frequency="weekly", time_of_day="09:00", days_of_week=[0]),  # Monday only
        auto_run_enabled=True,
        focus_areas=["trend_analysis", "content_opportunities"],
        generate_content_ideas=True,
    )

    # Sample 4: Competitor Intelligence
    competitor_intel_config = GoogleTrendsResearchConfig(
        user_id="user_002",
        workspace_id="workspace_002",
        config_name="competitor_intelligence",
        description="Monitor competitor brands and industry trends",
        trends_config=GoogleTrendsConfig(
            keywords=["Notion", "Airtable", "Monday.com", "Asana", "Trello", "ClickUp"],
            timeframe=TrendsTimeframe.LAST_30_DAYS,
            geo_location=TrendsGeoLocation.WORLDWIDE,
            category=TrendsCategory.COMPUTERS_ELECTRONICS,
            opportunity_types=[
                ContentOpportunityType.COMPARISON_TOPICS,
                ContentOpportunityType.RISING_SEARCHES,
                ContentOpportunityType.QUESTION_QUERIES,
            ],
            analysis_depth=AnalysisDepth.COMPREHENSIVE,
            enable_keyword_comparison=True,
            max_comparison_keywords=5,
            include_regional_data=True,
            target_content_types=["blog", "video"],
            target_audience="business professionals",
            content_urgency_level="normal",
        ),
        analysis_depth=AnalysisDepth.STANDARD,
        schedule=ResearchSchedule(frequency="weekly", time_of_day="11:00", days_of_week=[1, 4]),  # Tuesday and Friday
        auto_run_enabled=False,
        focus_areas=["competitive_intelligence", "trend_analysis"],
    )

    # Sample 5: YouTube Content Strategy
    youtube_strategy_config = GoogleTrendsResearchConfig(
        user_id="user_003",
        workspace_id="workspace_003",
        config_name="youtube_content_strategy",
        description="YouTube-focused content discovery and trend analysis",
        trends_config=GoogleTrendsConfig(
            keywords=["tutorial", "how to", "review", "unboxing", "vs", "best"],
            timeframe=TrendsTimeframe.LAST_7_DAYS,
            geo_location=TrendsGeoLocation.UNITED_STATES,
            category=TrendsCategory.ALL,
            opportunity_types=[
                ContentOpportunityType.VIDEO_OPPORTUNITIES,
                ContentOpportunityType.QUESTION_QUERIES,
                ContentOpportunityType.COMPARISON_TOPICS,
                ContentOpportunityType.BREAKOUT_TOPICS,
            ],
            analysis_depth=AnalysisDepth.COMPREHENSIVE,
            include_youtube_trends=True,
            include_news_trends=False,
            max_related_queries=25,
            target_content_types=["video"],
            target_audience="general",
            content_urgency_level="high",
        ),
        analysis_depth=AnalysisDepth.COMPREHENSIVE,
        schedule=ResearchSchedule(frequency="daily", time_of_day="07:00"),
        auto_run_enabled=True,
        focus_areas=["content_opportunities"],
        generate_content_ideas=True,
        export_formats=["json", "markdown"],
    )

    # Save sample configs
    configs = [
        tech_trends_config,
        content_discovery_config,
        seasonal_planning_config,
        competitor_intel_config,
        youtube_strategy_config,
    ]

    for config in configs:
        filepath = manager.create_config(config)
        print(f"Created sample config: {filepath}")

    return configs


if __name__ == "__main__":
    # Create sample configurations
    print("Creating sample Google Trends research configurations...")
    configs = create_sample_configs()
    print(f"Created {len(configs)} sample configurations")

    # Test loading a config
    manager = GoogleTrendsResearchConfigManager()
    loaded_config = manager.load_config("user_001", "tech_trends_monitoring")
    if loaded_config:
        print(f"Successfully loaded config: {loaded_config.config_name}")
        print(f"Keywords: {loaded_config.trends_config.keywords}")
        print(f"Timeframe: {loaded_config.trends_config.timeframe.value}")
    else:
        print("Failed to load config")
