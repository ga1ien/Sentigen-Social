#!/usr/bin/env python3
"""
Standardized Google Trends Research Tool
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
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Try to import pytrends, but make it optional
try:
    from pytrends.request import TrendReq

    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logger.warning("pytrends not available, Google Trends functionality will be limited")


class GoogleTrendsAPI:
    """Google Trends API client using pytrends"""

    def __init__(self):
        if not PYTRENDS_AVAILABLE:
            raise ImportError(
                "pytrends is required for Google Trends functionality. Install with: pip install pytrends"
            )

        self.pytrends = TrendReq(hl="en-US", tz=360)

    def get_interest_over_time(self, keywords: List[str], timeframe: str = "today 12-m") -> Dict[str, Any]:
        """Get interest over time for keywords"""
        try:
            self.pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo="", gprop="")
            data = self.pytrends.interest_over_time()

            if data.empty:
                return {"error": "No data available"}

            # Convert to JSON-serializable format
            result = {
                "timeframe": timeframe,
                "keywords": keywords,
                "data": data.to_dict("records"),
                "columns": list(data.columns),
            }

            return result

        except Exception as e:
            logger.error("Failed to get interest over time", error=str(e))
            return {"error": str(e)}

    def get_related_queries(self, keywords: List[str]) -> Dict[str, Any]:
        """Get related queries for keywords"""
        try:
            self.pytrends.build_payload(keywords, cat=0, timeframe="today 12-m", geo="", gprop="")
            related_queries = self.pytrends.related_queries()

            # Convert to JSON-serializable format
            result = {}
            for keyword in keywords:
                if keyword in related_queries:
                    keyword_data = related_queries[keyword]
                    result[keyword] = {}

                    if keyword_data["top"] is not None:
                        result[keyword]["top"] = keyword_data["top"].to_dict("records")
                    else:
                        result[keyword]["top"] = []

                    if keyword_data["rising"] is not None:
                        result[keyword]["rising"] = keyword_data["rising"].to_dict("records")
                    else:
                        result[keyword]["rising"] = []

            return result

        except Exception as e:
            logger.error("Failed to get related queries", error=str(e))
            return {"error": str(e)}

    def get_trending_searches(self, country: str = "united_states") -> Dict[str, Any]:
        """Get trending searches for a country"""
        try:
            trending_searches = self.pytrends.trending_searches(pn=country)

            if trending_searches.empty:
                return {"error": "No trending searches available"}

            # Convert to JSON-serializable format
            result = {
                "country": country,
                "trending_searches": trending_searches[0].tolist(),  # First column contains the searches
            }

            return result

        except Exception as e:
            logger.error("Failed to get trending searches", error=str(e))
            return {"error": str(e)}

    def get_top_charts(self, year: int, geo: str = "US", cat: str = "") -> Dict[str, Any]:
        """Get top charts for a year"""
        try:
            top_charts = self.pytrends.top_charts(year, hl="en-US", tz=300, geo=geo)

            if top_charts.empty:
                return {"error": "No top charts available"}

            # Convert to JSON-serializable format
            result = {"year": year, "geo": geo, "data": top_charts.to_dict("records")}

            return result

        except Exception as e:
            logger.error("Failed to get top charts", error=str(e))
            return {"error": str(e)}


class GoogleTrendsResearchTool(StandardizedResearchTool):
    """Standardized Google Trends research tool implementation"""

    def __init__(self):
        super().__init__(DataSource.GOOGLE_TRENDS)
        self.trends_api = None
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the Google Trends research tool"""
        await super().initialize()

        try:
            logger.info("Initializing Google Trends research tool")

            if not PYTRENDS_AVAILABLE:
                raise ImportError("pytrends is required for Google Trends functionality")

            # Initialize Google Trends API client
            self.trends_api = GoogleTrendsAPI()

            logger.info("Google Trends research tool initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Google Trends research tool", error=str(e))
            raise

    async def collect_raw_data(self, config: ResearchConfig) -> Dict[str, Any]:
        """Collect raw data from Google Trends"""
        try:
            logger.info("Starting Google Trends data collection", query=config.query)

            # Parse keywords from query
            keywords = config.custom_parameters.get("keywords", [config.query])
            if isinstance(keywords, str):
                keywords = [keywords]

            # Limit to 5 keywords (Google Trends API limitation)
            keywords = keywords[:5]

            timeframe = config.custom_parameters.get("timeframe", "today 12-m")
            country = config.custom_parameters.get("country", "united_states")
            include_related = config.custom_parameters.get("include_related", True)
            include_trending = config.custom_parameters.get("include_trending", True)

            collected_data = {"keywords": keywords, "timeframe": timeframe, "country": country}

            # Get interest over time
            logger.info("Getting interest over time", keywords=keywords)
            interest_data = self.trends_api.get_interest_over_time(keywords, timeframe)
            collected_data["interest_over_time"] = interest_data

            # Get related queries if requested
            if include_related:
                logger.info("Getting related queries")
                related_data = self.trends_api.get_related_queries(keywords)
                collected_data["related_queries"] = related_data

            # Get trending searches if requested
            if include_trending:
                logger.info("Getting trending searches")
                trending_data = self.trends_api.get_trending_searches(country)
                collected_data["trending_searches"] = trending_data

            # Get top charts for current year
            current_year = datetime.now().year
            logger.info("Getting top charts", year=current_year)
            top_charts_data = self.trends_api.get_top_charts(current_year)
            collected_data["top_charts"] = top_charts_data

            raw_data = {
                "source": "google_trends",
                "query": config.query,
                "data": collected_data,
                "collection_metadata": {
                    "keywords": keywords,
                    "timeframe": timeframe,
                    "country": country,
                    "include_related": include_related,
                    "include_trending": include_trending,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                },
            }

            logger.info("Google Trends data collection completed")
            return raw_data

        except Exception as e:
            logger.error("Google Trends data collection failed", error=str(e))
            raise

    async def run_research(self, config: ResearchConfig) -> ResearchResult:
        """Run complete research workflow with enhanced analysis"""
        logger.info("Starting Google Trends research", query=config.query)

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

            # Step 3: Enhanced AI analysis for Google Trends
            if config.analysis_depth != AnalysisDepth.BASIC:
                analyzed_data = await self._analyze_google_trends_data(raw_data, config)
                result.analyzed_data = analyzed_data

            # Step 4: Save to database
            await self.db_manager.save_research_result(result)

            # Step 5: Save to local file (Google Trends-specific feature)
            await self._save_local_results(result)

            logger.info("Google Trends research completed", result_id=result.id)
            return result

        except Exception as e:
            logger.error("Google Trends research failed", error=str(e))
            raise

    async def _analyze_google_trends_data(self, raw_data: Dict[str, Any], config: ResearchConfig) -> Dict[str, Any]:
        """Enhanced Google Trends-specific analysis using Pydantic AI"""
        try:
            trends_data = raw_data.get("data", {})

            # Prepare content for analysis
            analysis_content = f"""
Google Trends Analysis for: {config.query}
Keywords: {', '.join(trends_data.get('keywords', []))}
Timeframe: {trends_data.get('timeframe', 'Unknown')}
Country: {trends_data.get('country', 'Unknown')}
"""

            # Add interest over time summary
            interest_data = trends_data.get("interest_over_time", {})
            if "data" in interest_data and interest_data["data"]:
                analysis_content += f"\nInterest Over Time Data Points: {len(interest_data['data'])}"

                # Get recent trends
                recent_data = interest_data["data"][-5:] if len(interest_data["data"]) >= 5 else interest_data["data"]
                analysis_content += f"\nRecent Trend Data: {json.dumps(recent_data, default=str)[:500]}"

            # Add related queries
            related_queries = trends_data.get("related_queries", {})
            if related_queries:
                analysis_content += "\n\nRelated Queries:"
                for keyword, queries in related_queries.items():
                    if queries.get("top"):
                        top_queries = [q.get("query", "") for q in queries["top"][:5]]
                        analysis_content += f"\nTop queries for '{keyword}': {', '.join(top_queries)}"
                    if queries.get("rising"):
                        rising_queries = [q.get("query", "") for q in queries["rising"][:5]]
                        analysis_content += f"\nRising queries for '{keyword}': {', '.join(rising_queries)}"

            # Add trending searches
            trending_searches = trends_data.get("trending_searches", {})
            if trending_searches and "trending_searches" in trending_searches:
                top_trending = trending_searches["trending_searches"][:10]
                analysis_content += f"\n\nCurrent Trending Searches: {', '.join(top_trending)}"

            # Add top charts
            top_charts = trends_data.get("top_charts", {})
            if top_charts and "data" in top_charts:
                chart_titles = [item.get("title", "") for item in top_charts["data"][:10]]
                analysis_content += f"\n\nTop Charts: {', '.join(chart_titles)}"

            # Use the standardized agent for analysis
            analysis = await self.agent.analyze_data({"content": analysis_content, "trends_data": trends_data}, config)

            # Generate summary
            summary = self._generate_summary(trends_data)

            return {
                "ai_analysis": analysis,
                "summary": summary,
                "analysis_metadata": {
                    "analysis_depth": config.analysis_depth.value,
                    "model_used": self.agent.model_name,
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                },
            }

        except Exception as e:
            logger.error("Google Trends data analysis failed", error=str(e))
            return {"error": str(e), "analyzed_at": datetime.now(timezone.utc).isoformat()}

    def _generate_summary(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics"""
        try:
            summary = {
                "keywords_analyzed": len(trends_data.get("keywords", [])),
                "timeframe": trends_data.get("timeframe", "Unknown"),
                "country": trends_data.get("country", "Unknown"),
            }

            # Interest over time summary
            interest_data = trends_data.get("interest_over_time", {})
            if "data" in interest_data and interest_data["data"]:
                data_points = interest_data["data"]
                summary["interest_data_points"] = len(data_points)

                # Calculate trend direction (simple comparison of first vs last values)
                if len(data_points) >= 2:
                    keywords = trends_data.get("keywords", [])
                    if keywords:
                        first_keyword = keywords[0]
                        if first_keyword in data_points[0] and first_keyword in data_points[-1]:
                            first_value = data_points[0].get(first_keyword, 0)
                            last_value = data_points[-1].get(first_keyword, 0)
                            if last_value > first_value:
                                summary["trend_direction"] = "increasing"
                            elif last_value < first_value:
                                summary["trend_direction"] = "decreasing"
                            else:
                                summary["trend_direction"] = "stable"

            # Related queries summary
            related_queries = trends_data.get("related_queries", {})
            if related_queries:
                total_top_queries = 0
                total_rising_queries = 0
                for keyword, queries in related_queries.items():
                    if queries.get("top"):
                        total_top_queries += len(queries["top"])
                    if queries.get("rising"):
                        total_rising_queries += len(queries["rising"])

                summary["total_top_related_queries"] = total_top_queries
                summary["total_rising_related_queries"] = total_rising_queries

            # Trending searches summary
            trending_searches = trends_data.get("trending_searches", {})
            if trending_searches and "trending_searches" in trending_searches:
                summary["trending_searches_count"] = len(trending_searches["trending_searches"])

            # Top charts summary
            top_charts = trends_data.get("top_charts", {})
            if top_charts and "data" in top_charts:
                summary["top_charts_count"] = len(top_charts["data"])

            return summary

        except Exception as e:
            logger.error("Failed to generate summary", error=str(e))
            return {"error": str(e)}

    async def _save_local_results(self, result: ResearchResult) -> None:
        """Save results to local file (Google Trends-specific feature)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"standardized_google_trends_research_{timestamp}.json"
            filepath = self.results_dir / filename

            with open(filepath, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)

            logger.info("Results saved to local file", filepath=str(filepath))

        except Exception as e:
            logger.error("Failed to save local results", error=str(e))


# CLI Interface
async def main():
    """Main CLI function"""
    await run_standardized_cli(GoogleTrendsResearchTool, DataSource.GOOGLE_TRENDS)


if __name__ == "__main__":
    exit(asyncio.run(main()))
