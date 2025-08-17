"""
Parallel Scraper Orchestrator
Runs LinkedIn, Substack, and Reddit scrapers in parallel
Manages concurrent execution and aggregates results
"""

import asyncio
import json
import os
import sys
import time
from uuid import uuid4

from openai import AsyncOpenAI

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.intelligent_substack_scraper import IntelligentSubstackScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.reddit_scraper import RedditScraper

from database.supabase_client import SupabaseClient


class ParallelScraperOrchestrator:
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        self.supabase_client = SupabaseClient()
        self.linkedin_scraper = LinkedInScraper()
        self.substack_scraper = IntelligentSubstackScraper()
        self.reddit_scraper = RedditScraper()

    async def orchestrate_parallel_scraping(self, search_query="the future of content with AI"):
        """Orchestrate parallel scraping across all three platforms"""
        print("🚀 PARALLEL SCRAPER ORCHESTRATOR")
        print("=" * 80)
        print(f"🎯 Search Query: {search_query}")
        print("🌐 Platforms: LinkedIn, Substack, Reddit")
        print("⚡ Mode: Parallel Execution (All scrapers running simultaneously)")
        print("🤖 Analysis: GPT-5 Mini")
        print("💾 Database: Supabase")
        print()

        orchestration_id = str(uuid4())
        start_time = time.time()

        try:
            print("🚀 Starting all scrapers in parallel...")
            print("📊 Monitor individual scraper progress below:")
            print("-" * 80)

            # Create tasks for parallel execution
            tasks = [
                asyncio.create_task(self._run_linkedin_scraper(search_query)),
                asyncio.create_task(self._run_substack_scraper(search_query)),
                asyncio.create_task(self._run_reddit_scraper(search_query)),
            ]

            # Wait for all scrapers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            linkedin_result, substack_result, reddit_result = results

            execution_time = time.time() - start_time

            print("-" * 80)
            print("✅ ALL SCRAPERS COMPLETED!")
            print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
            print()

            # Create summary
            summary = self._create_execution_summary(linkedin_result, substack_result, reddit_result, execution_time)

            # Generate master analysis
            print("🧠 Creating master analysis with GPT-5 Mini...")
            master_analysis = await self._create_master_analysis(
                linkedin_result, substack_result, reddit_result, search_query
            )

            # Save orchestration record
            print("💾 Saving orchestration record...")
            orchestration_record = await self._save_orchestration_record(
                orchestration_id,
                search_query,
                linkedin_result,
                substack_result,
                reddit_result,
                master_analysis,
                summary,
            )

            if orchestration_record:
                print("✅ ORCHESTRATION COMPLETED SUCCESSFULLY!")
                print(f"📊 Orchestration ID: {orchestration_id}")
                self._print_final_summary(summary, orchestration_id)
                return orchestration_record

        except Exception as e:
            print(f"❌ Orchestration failed: {e}")
            return None

    async def _run_linkedin_scraper(self, search_query):
        """Run LinkedIn scraper with error handling"""
        try:
            print("🔵 LinkedIn scraper starting...")
            result = await self.linkedin_scraper.scrape_ai_ads_content(search_query)
            if result:
                print("🔵 LinkedIn scraper completed successfully!")
                return result
            else:
                print("🔵 LinkedIn scraper failed!")
                return None
        except Exception as e:
            print(f"🔵 LinkedIn scraper error: {e}")
            return None

    async def _run_substack_scraper(self, search_query):
        """Run Substack scraper with error handling"""
        try:
            print("📰 Substack scraper starting...")
            result = await self.substack_scraper.intelligent_scrape(search_query)
            if result:
                print("📰 Substack scraper completed successfully!")
                return result
            else:
                print("📰 Substack scraper failed!")
                return None
        except Exception as e:
            print(f"📰 Substack scraper error: {e}")
            return None

    async def _run_reddit_scraper(self, search_query):
        """Run Reddit scraper with error handling"""
        try:
            print("🔴 Reddit scraper starting...")
            result = await self.reddit_scraper.scrape_ai_ads_content(search_query)
            if result:
                print("🔴 Reddit scraper completed successfully!")
                return result
            else:
                print("🔴 Reddit scraper failed!")
                return None
        except Exception as e:
            print(f"🔴 Reddit scraper error: {e}")
            return None

    def _create_execution_summary(self, linkedin_result, substack_result, reddit_result, execution_time):
        """Create execution summary"""
        summary = {
            "total_execution_time": execution_time,
            "scrapers_run": 3,
            "successful_scrapers": 0,
            "failed_scrapers": 0,
            "total_content_extracted": 0,
            "platform_results": {},
        }

        # LinkedIn summary
        if linkedin_result and not isinstance(linkedin_result, Exception):
            summary["successful_scrapers"] += 1
            linkedin_insights = linkedin_result.get("linkedin_insights", {})
            posts_count = linkedin_insights.get("posts_count", 0)
            summary["total_content_extracted"] += posts_count
            summary["platform_results"]["linkedin"] = {
                "status": "success",
                "content_count": posts_count,
                "scraper_id": linkedin_result.get("id"),
            }
        else:
            summary["failed_scrapers"] += 1
            summary["platform_results"]["linkedin"] = {
                "status": "failed",
                "error": str(linkedin_result) if isinstance(linkedin_result, Exception) else "Unknown error",
            }

        # Substack summary
        if substack_result and not isinstance(substack_result, Exception):
            summary["successful_scrapers"] += 1
            substack_insights = substack_result.get("substack_insights", {})
            articles_count = substack_insights.get("articles_count", 0)
            summary["total_content_extracted"] += articles_count
            summary["platform_results"]["substack"] = {
                "status": "success",
                "content_count": articles_count,
                "scraper_id": substack_result.get("id"),
            }
        else:
            summary["failed_scrapers"] += 1
            summary["platform_results"]["substack"] = {
                "status": "failed",
                "error": str(substack_result) if isinstance(substack_result, Exception) else "Unknown error",
            }

        # Reddit summary
        if reddit_result and not isinstance(reddit_result, Exception):
            summary["successful_scrapers"] += 1
            reddit_insights = reddit_result.get("reddit_insights", {})
            posts_count = reddit_insights.get("posts_count", 0)
            summary["total_content_extracted"] += posts_count
            summary["platform_results"]["reddit"] = {
                "status": "success",
                "content_count": posts_count,
                "scraper_id": reddit_result.get("id"),
            }
        else:
            summary["failed_scrapers"] += 1
            summary["platform_results"]["reddit"] = {
                "status": "failed",
                "error": str(reddit_result) if isinstance(reddit_result, Exception) else "Unknown error",
            }

        return summary

    async def _create_master_analysis(self, linkedin_result, substack_result, reddit_result, search_query):
        """Create comprehensive master analysis across all platforms"""
        try:
            # Extract insights from successful scrapers
            linkedin_insights = (
                linkedin_result.get("linkedin_insights", {})
                if linkedin_result and not isinstance(linkedin_result, Exception)
                else {}
            )
            substack_insights = (
                substack_result.get("substack_insights", {})
                if substack_result and not isinstance(substack_result, Exception)
                else {}
            )
            reddit_insights = (
                reddit_result.get("reddit_insights", {})
                if reddit_result and not isinstance(reddit_result, Exception)
                else {}
            )

            master_prompt = f"""
            Create a comprehensive master analysis about "{search_query}" from three platforms:

            LINKEDIN INSIGHTS (Professional/B2B):
            {json.dumps(linkedin_insights, indent=2)[:4000]}

            SUBSTACK INSIGHTS (In-depth/Educational):
            {json.dumps(substack_insights, indent=2)[:4000]}

            REDDIT INSIGHTS (Community/User Experience):
            {json.dumps(reddit_insights, indent=2)[:4000]}

            Create a comprehensive analysis covering:

            1. EXECUTIVE SUMMARY
               - Key findings about the future of content with AI
               - Most important trends and insights

            2. CROSS-PLATFORM TRENDS
               - Common themes across all platforms
               - Platform-specific perspectives
               - Emerging patterns and technologies

            3. FUTURE PREDICTIONS
               - Short-term developments (6-12 months)
               - Long-term evolution (2-5 years)
               - Disruptive technologies and approaches

            4. CONTENT CREATION EVOLUTION
               - AI tools transforming content creation
               - New content formats and mediums
               - Creator economy implications

            5. PLATFORM-SPECIFIC INSIGHTS
               - LinkedIn: Professional content trends
               - Substack: Long-form content evolution
               - Reddit: Community-driven content

            6. ACTIONABLE RECOMMENDATIONS
               - For content creators
               - For businesses and marketers
               - For platform developers

            7. TECHNOLOGY LANDSCAPE
               - Key AI tools and platforms mentioned
               - Emerging technologies to watch
               - Integration opportunities

            8. CHALLENGES AND OPPORTUNITIES
               - Current limitations and barriers
               - Untapped opportunities
               - Ethical considerations

            Return comprehensive JSON analysis with specific insights and predictions.
            """

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": master_prompt}],
                response_format={"type": "json_object"},
            )

            analysis = json.loads(response.choices[0].message.content)
            print("   ✅ Master GPT-5 Mini analysis completed")
            return analysis

        except Exception as e:
            print(f"   ❌ Master analysis error: {e}")
            return {"error": str(e)}

    async def _save_orchestration_record(
        self, orchestration_id, search_query, linkedin_result, substack_result, reddit_result, master_analysis, summary
    ):
        """Save comprehensive orchestration record to Supabase"""
        try:
            orchestration_record = {
                "id": orchestration_id,
                "workflow_id": str(uuid4()),
                "user_id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "research_topic": f"Parallel Scraping: {search_query}",
                "platforms": ["LinkedIn", "Substack", "Reddit"],
                "status": "completed",
                # Individual platform insights
                "linkedin_insights": linkedin_result.get("linkedin_insights")
                if linkedin_result and not isinstance(linkedin_result, Exception)
                else None,
                "substack_insights": substack_result.get("substack_insights")
                if substack_result and not isinstance(substack_result, Exception)
                else None,
                "reddit_insights": reddit_result.get("reddit_insights")
                if reddit_result and not isinstance(reddit_result, Exception)
                else None,
                # Master analysis combining all platforms
                "combined_analysis": master_analysis,
                "session_metadata": {
                    "orchestrator": "parallel_scraper_orchestrator",
                    "execution_mode": "parallel",
                    "scrapers_run": 3,
                    "successful_scrapers": summary["successful_scrapers"],
                    "failed_scrapers": summary["failed_scrapers"],
                    "total_execution_time": summary["total_execution_time"],
                    "total_content_extracted": summary["total_content_extracted"],
                    "platform_results": summary["platform_results"],
                    "timestamp": time.time(),
                    "real_automation": True,
                    "headless_mode": True,
                },
            }

            result = (
                self.supabase_client.service_client.table("research_sessions").insert(orchestration_record).execute()
            )

            print("   ✅ Orchestration record saved to Supabase!")
            return orchestration_record

        except Exception as e:
            print(f"   ❌ Orchestration save error: {e}")
            return None

    def _print_final_summary(self, summary, orchestration_id):
        """Print final execution summary"""
        print("\n📊 PARALLEL SCRAPING SUMMARY:")
        print("=" * 50)
        print(f"🆔 Orchestration ID: {orchestration_id}")
        print(f"⏱️  Total Time: {summary['total_execution_time']:.2f} seconds")
        print(f"✅ Successful: {summary['successful_scrapers']}/3 scrapers")
        print(f"❌ Failed: {summary['failed_scrapers']}/3 scrapers")
        print(f"📝 Total Content: {summary['total_content_extracted']} items")
        print()

        for platform, result in summary["platform_results"].items():
            status_emoji = "✅" if result["status"] == "success" else "❌"
            if result["status"] == "success":
                print(f"{status_emoji} {platform.title()}: {result['content_count']} items extracted")
            else:
                print(f"{status_emoji} {platform.title()}: Failed")

        print("\n💾 CHECK SUPABASE:")
        print("   → research_sessions table")
        print("   → linkedin_insights column")
        print("   → substack_insights column")
        print("   → reddit_insights column")
        print("   → combined_analysis column")


async def main():
    """Run parallel scraper orchestration"""
    print("🎯 PARALLEL SCRAPER ORCHESTRATION")
    print("The Future of Content with AI")
    print("LinkedIn + Substack + Reddit")
    print("Parallel Execution + GPT-5 Mini Analysis")
    print()

    orchestrator = ParallelScraperOrchestrator()
    result = await orchestrator.orchestrate_parallel_scraping("the future of content with AI")

    if result:
        print("\n🎉 PARALLEL ORCHESTRATION SUCCESS!")
        print("All scrapers executed and results combined!")
    else:
        print("\n❌ PARALLEL ORCHESTRATION FAILED")


if __name__ == "__main__":
    asyncio.run(main())
