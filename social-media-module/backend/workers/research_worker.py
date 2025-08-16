"""
Research Worker using Perplexity AI for information gathering and research tasks.
"""

import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from dotenv import load_dotenv

from workers.base_worker import BaseWorker, WorkerTask, WorkerResult

load_dotenv()

logger = structlog.get_logger(__name__)


class ResearchWorker(BaseWorker):
    """Worker specialized for research and information gathering using Perplexity AI."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("research_worker", config)
    
    def _initialize_config(self):
        """Initialize Perplexity-specific configuration."""
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
        self.model = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")
        
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not found - research worker will be disabled")
            return
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.config.update({
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model
        })
    
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process a research task using Perplexity AI.
        
        Args:
            task: Research task containing query and parameters
            
        Returns:
            WorkerResult with research findings
        """
        if not self.api_key:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message="Perplexity API key not configured"
            )
        
        try:
            # Extract research parameters
            query = task.input_data.get("query", "")
            search_focus = task.input_data.get("search_focus", "general")
            max_results = task.input_data.get("max_results", 5)
            include_sources = task.input_data.get("include_sources", True)
            
            if not query:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message="No query provided for research"
                )
            
            # Build the research prompt
            system_prompt = self._build_research_prompt(search_focus)
            
            # Make API call to Perplexity
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2,
                    "return_citations": include_sources,
                    "return_images": False
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                result_data = response.json()
                
                # Extract research results
                content = result_data["choices"][0]["message"]["content"]
                citations = result_data.get("citations", []) if include_sources else []
                
                research_result = {
                    "query": query,
                    "findings": content,
                    "sources": citations,
                    "search_focus": search_focus,
                    "model_used": self.model,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(
                    "Research task completed successfully",
                    task_id=task.task_id,
                    query_length=len(query),
                    findings_length=len(content),
                    sources_count=len(citations)
                )
                
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="success",
                    result=research_result,
                    metadata={
                        "model": self.model,
                        "sources_count": len(citations),
                        "content_length": len(content)
                    }
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = f"Perplexity API error: {e.response.status_code}"
            try:
                error_response = e.response.json()
                error_detail += f" - {error_response.get('error', {}).get('message', str(e))}"
            except:
                error_detail += f" - {str(e)}"
            
            logger.error("Research task failed", task_id=task.task_id, error=error_detail)
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=error_detail
            )
            
        except Exception as e:
            logger.error("Unexpected error in research task", task_id=task.task_id, error=str(e))
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Research failed: {str(e)}"
            )
    
    def _build_research_prompt(self, search_focus: str) -> str:
        """Build a research prompt based on the search focus."""
        base_prompt = """You are a professional research assistant specializing in gathering accurate, up-to-date information from reliable sources. Your task is to provide comprehensive, well-structured research findings."""
        
        focus_prompts = {
            "social_media": "Focus on social media trends, platform updates, engagement strategies, and digital marketing insights.",
            "news": "Focus on current news, recent developments, and breaking stories. Prioritize credible news sources.",
            "trends": "Focus on trending topics, viral content, popular discussions, and emerging patterns.",
            "competitors": "Focus on competitor analysis, market positioning, and industry benchmarking.",
            "audience": "Focus on audience insights, demographics, behavior patterns, and preferences.",
            "content": "Focus on content ideas, creative inspiration, and successful content examples.",
            "general": "Provide comprehensive research covering all relevant aspects of the topic."
        }
        
        specific_prompt = focus_prompts.get(search_focus, focus_prompts["general"])
        
        return f"""{base_prompt}

{specific_prompt}

Structure your response as follows:
1. **Key Findings**: Main insights and important information
2. **Details**: Comprehensive information with context
3. **Sources**: Reference credible sources when available
4. **Actionable Insights**: Practical takeaways and recommendations

Be thorough, accurate, and cite sources when possible."""
    
    async def health_check(self) -> bool:
        """Check if Perplexity API is accessible."""
        if not self.api_key:
            self.is_healthy = False
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Simple test query
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "Hello, this is a health check."}
                    ],
                    "max_tokens": 10
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers
                )
                
                self.is_healthy = response.status_code == 200
                self.last_health_check = datetime.utcnow()
                
                return self.is_healthy
                
        except Exception as e:
            logger.warning("Research worker health check failed", error=str(e))
            self.is_healthy = False
            self.last_health_check = datetime.utcnow()
            return False
    
    async def research_trending_topics(self, category: str = "general") -> Dict[str, Any]:
        """
        Research current trending topics in a specific category.
        
        Args:
            category: Category to research trends for
            
        Returns:
            Dictionary with trending topics and insights
        """
        task = WorkerTask(
            task_id=f"trending_{category}_{datetime.utcnow().timestamp()}",
            task_type="trending_research",
            input_data={
                "query": f"What are the current trending topics and discussions in {category}? Include recent developments and popular conversations.",
                "search_focus": "trends",
                "max_results": 10,
                "include_sources": True
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None
    
    async def research_competitor_content(self, competitor: str, platform: str = "general") -> Dict[str, Any]:
        """
        Research competitor content and strategies.
        
        Args:
            competitor: Competitor name or brand
            platform: Specific platform to focus on
            
        Returns:
            Dictionary with competitor insights
        """
        task = WorkerTask(
            task_id=f"competitor_{competitor}_{datetime.utcnow().timestamp()}",
            task_type="competitor_research",
            input_data={
                "query": f"Research {competitor}'s recent content strategy and performance on {platform}. Include their posting patterns, engagement tactics, and successful content types.",
                "search_focus": "competitors",
                "max_results": 8,
                "include_sources": True
            }
        )
        
        result = await self.process_task(task)
        return result.result if result.status == "success" else None