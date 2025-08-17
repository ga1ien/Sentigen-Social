#!/usr/bin/env python3
"""
Standardized Research Tool Template
Based on Project Server Standards v1.0

This template provides the structure for creating research tools that comply with:
- Python 3.11+ environment
- Pydantic AI v0.3.2+ agent framework
- FastAPI v0.115.13+ for APIs
- Supabase with asyncpg for database
- Proper async/await patterns
- Snake_case naming conventions
- Environment variable management with dotenv
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Core dependencies (Project Server Standards compliant)
import asyncpg
import structlog
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# Configuration Enums
class AnalysisDepth(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class ResearchFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class DataSource(str, Enum):
    REDDIT = "reddit"
    GITHUB = "github"
    HACKERNEWS = "hackernews"
    GOOGLE_TRENDS = "google_trends"


# Pydantic Models (snake_case naming)
@dataclass
class ResearchConfig:
    """Standardized research configuration"""

    source: DataSource
    query: str
    max_items: int = 10
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    frequency: ResearchFrequency = ResearchFrequency.DAILY
    workspace_id: str = "00000000-0000-0000-0000-000000000001"
    user_id: str = "00000000-0000-0000-0000-000000000001"
    custom_parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_parameters is None:
            self.custom_parameters = {}


class ResearchResult(BaseModel):
    """Standardized research result model"""

    id: str = Field(..., description="Unique result identifier")
    source: DataSource = Field(..., description="Data source")
    query: str = Field(..., description="Research query")
    raw_data: Dict[str, Any] = Field(..., description="Raw collected data")
    analyzed_data: Optional[Dict[str, Any]] = Field(None, description="AI analyzed data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workspace_id: str = Field(..., description="Workspace identifier")
    user_id: str = Field(..., description="User identifier")


class DatabaseManager:
    """Standardized database manager using asyncpg and Supabase"""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.connection_pool: Optional[asyncpg.Pool] = None

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    async def initialize(self) -> None:
        """Initialize database connection pool"""
        try:
            # Extract database URL from Supabase URL
            db_url = self.supabase_url.replace("https://", "postgresql://postgres:")
            db_url = f"{db_url.split('.')[0]}.pooler.supabase.com:6543/postgres"

            self.connection_pool = await asyncpg.create_pool(
                db_url, password=self.supabase_key, min_size=1, max_size=10, command_timeout=60
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise

    async def close(self) -> None:
        """Close database connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Database connection pool closed")

    async def save_research_result(self, result: ResearchResult) -> bool:
        """Save research result to database"""
        if not self.connection_pool:
            await self.initialize()

        try:
            async with self.connection_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO research_results
                    (id, source, query, raw_data, analyzed_data, metadata, created_at, workspace_id, user_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (id) DO UPDATE SET
                        analyzed_data = EXCLUDED.analyzed_data,
                        metadata = EXCLUDED.metadata
                """,
                    result.id,
                    result.source.value,
                    result.query,
                    json.dumps(result.raw_data),
                    json.dumps(result.analyzed_data) if result.analyzed_data else None,
                    json.dumps(result.metadata),
                    result.created_at,
                    result.workspace_id,
                    result.user_id,
                )
            logger.info("Research result saved", result_id=result.id)
            return True
        except Exception as e:
            logger.error("Failed to save research result", error=str(e), result_id=result.id)
            return False


class StandardizedResearchAgent:
    """Standardized research agent using Pydantic AI"""

    def __init__(self, source: DataSource):
        self.source = source
        self.model_name: KnownModelName = os.getenv("LLM_CHOICE", "gpt-4o-mini")

        # Initialize Pydantic AI agent
        self.agent = Agent(model=self.model_name, system_prompt=self._get_system_prompt(), deps_type=Dict[str, Any])

    def _get_system_prompt(self) -> str:
        """Get source-specific system prompt"""
        prompts = {
            DataSource.REDDIT: """You are a Reddit research analyst. Analyze Reddit posts and comments to extract insights about trends, discussions, and community sentiment. Focus on identifying key themes, popular opinions, and emerging topics.""",
            DataSource.GITHUB: """You are a GitHub research analyst. Analyze repositories, issues, and discussions to extract insights about technology trends, developer tools, and open source projects. Focus on identifying viral projects, technology adoption patterns, and developer community needs.""",
            DataSource.HACKERNEWS: """You are a Hacker News research analyst. Analyze stories and comments to extract insights about technology trends, startup ecosystem, and developer community discussions. Focus on identifying emerging technologies, business opportunities, and industry sentiment.""",
            DataSource.GOOGLE_TRENDS: """You are a Google Trends research analyst. Analyze search trends and related queries to extract insights about public interest, seasonal patterns, and emerging topics. Focus on identifying trending topics, geographic patterns, and temporal trends.""",
        }
        return prompts.get(self.source, "You are a research analyst.")

    async def analyze_data(self, raw_data: Dict[str, Any], config: ResearchConfig) -> Dict[str, Any]:
        """Analyze raw data using Pydantic AI agent"""
        try:
            # Prepare analysis context
            context = {
                "source": self.source.value,
                "query": config.query,
                "analysis_depth": config.analysis_depth.value,
                "raw_data": raw_data,
            }

            # Run analysis with Pydantic AI
            result = await self.agent.run(
                f"Analyze this {self.source.value} data for the query '{config.query}' with {config.analysis_depth.value} depth analysis.",
                deps=context,
            )

            return {
                "analysis": result.data,
                "model_used": self.model_name,
                "analysis_depth": config.analysis_depth.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error("Analysis failed", error=str(e), source=self.source.value)
            return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}


class StandardizedResearchTool:
    """Base class for standardized research tools"""

    def __init__(self, source: DataSource):
        self.source = source
        self.db_manager = DatabaseManager()
        self.agent = StandardizedResearchAgent(source)
        self.session_id = f"{source.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def initialize(self) -> None:
        """Initialize the research tool"""
        await self.db_manager.initialize()
        logger.info("Research tool initialized", source=self.source.value)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        await self.db_manager.close()
        logger.info("Research tool cleaned up", source=self.source.value)

    async def collect_raw_data(self, config: ResearchConfig) -> Dict[str, Any]:
        """Collect raw data - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement collect_raw_data")

    async def run_research(self, config: ResearchConfig) -> ResearchResult:
        """Run complete research workflow"""
        logger.info("Starting research", source=self.source.value, query=config.query)

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

            # Step 3: AI analysis
            if config.analysis_depth != AnalysisDepth.BASIC:
                analyzed_data = await self.agent.analyze_data(raw_data, config)
                result.analyzed_data = analyzed_data

            # Step 4: Save to database
            await self.db_manager.save_research_result(result)

            logger.info("Research completed", result_id=result.id)
            return result

        except Exception as e:
            logger.error("Research failed", error=str(e), source=self.source.value)
            raise


def create_standardized_cli_parser(source: DataSource) -> argparse.ArgumentParser:
    """Create standardized CLI argument parser"""
    parser = argparse.ArgumentParser(
        description=f"Standardized {source.value.title()} Research Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Basic usage
  python cli_{source.value}_standardized.py --query "AI tools"

  # Custom parameters
  python cli_{source.value}_standardized.py --query "machine learning" --max-items 20 --analysis-depth comprehensive

  # Background execution
  python cli_{source.value}_standardized.py --query "startup trends" --daemon
        """,
    )

    parser.add_argument("--query", "-q", required=True, help=f"Search query for {source.value} research")

    parser.add_argument("--max-items", "-m", type=int, default=10, help="Maximum items to collect")

    parser.add_argument(
        "--analysis-depth",
        "-a",
        choices=[depth.value for depth in AnalysisDepth],
        default=AnalysisDepth.STANDARD.value,
        help="Analysis depth level",
    )

    parser.add_argument(
        "--frequency",
        "-f",
        choices=[freq.value for freq in ResearchFrequency],
        default=ResearchFrequency.DAILY.value,
        help="Research frequency",
    )

    parser.add_argument("--workspace-id", default="00000000-0000-0000-0000-000000000001", help="Workspace ID")

    parser.add_argument("--user-id", default="00000000-0000-0000-0000-000000000001", help="User ID")

    parser.add_argument("--config", "-c", help="Path to JSON config file")

    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon process")

    parser.add_argument("--output", "-o", help="Output file path for results")

    return parser


async def run_standardized_cli(tool_class, source: DataSource):
    """Run standardized CLI interface"""
    parser = create_standardized_cli_parser(source)
    args = parser.parse_args()

    # Load config from file if provided
    if args.config:
        with open(args.config, "r") as f:
            config_data = json.load(f)
    else:
        config_data = {}

    # Create research configuration
    config = ResearchConfig(
        source=source,
        query=args.query,
        max_items=args.max_items,
        analysis_depth=AnalysisDepth(args.analysis_depth),
        frequency=ResearchFrequency(args.frequency),
        workspace_id=args.workspace_id,
        user_id=args.user_id,
        custom_parameters=config_data.get("custom_parameters", {}),
    )

    # Initialize and run tool
    tool = tool_class(source)

    try:
        await tool.initialize()
        result = await tool.run_research(config)

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
            logger.info("Results saved", output_file=args.output)
        else:
            print(json.dumps(result.model_dump(), indent=2, default=str))

        return 0

    except Exception as e:
        logger.error("CLI execution failed", error=str(e))
        return 1
    finally:
        await tool.cleanup()


if __name__ == "__main__":
    print("This is a template file. Use it to create standardized research tools.")
    print("Example usage:")
    print("  1. Inherit from StandardizedResearchTool")
    print("  2. Implement collect_raw_data method")
    print("  3. Use run_standardized_cli for CLI interface")
