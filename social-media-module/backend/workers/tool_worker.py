"""
Tool Worker using GPT-5 Mini for function calling and tool execution.
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import structlog
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass

from .base_worker import BaseWorker, WorkerTask, WorkerResult
from ..utils import get_smart_model, AyrshareClient

load_dotenv()

logger = structlog.get_logger(__name__)


@dataclass
class ToolWorkerDeps:
    """Dependencies for the tool worker."""
    context: str
    available_tools: List[str]
    ayrshare_client: Optional[AyrshareClient] = None
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None


class ToolWorker(BaseWorker):
    """Worker specialized for tool calling and function execution using GPT-5 Mini."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("tool_worker", config)
        self._initialize_agent()
        self._initialize_tools()
    
    def _initialize_config(self):
        """Initialize GPT-5 Mini specific configuration."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found - tool worker will be disabled")
            return
        
        self.config.update({
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url
        })
    
    def _initialize_tools(self):
        """Initialize available tools for the worker."""
        self.available_tools = {}
        
        # Initialize Ayrshare client if available
        try:
            self.ayrshare_client = AyrshareClient()
            self.available_tools["ayrshare"] = self.ayrshare_client
        except Exception as e:
            logger.warning("Failed to initialize Ayrshare client", error=str(e))
            self.ayrshare_client = None
    
    def _initialize_agent(self):
        """Initialize the GPT-5 Mini agent for tool calling."""
        if not self.api_key:
            self.agent = None
            return
        
        # Set environment variables for the model configuration
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = self.api_key
        os.environ["OPENAI_MODEL"] = self.model
        
        system_prompt = """
        ~~ CONTEXT: ~~
        You are a specialized tool execution agent that excels at function calling and API interactions. You have access to various tools and services to accomplish tasks efficiently and accurately.

        ~~ GOAL: ~~
        Execute functions and tools to accomplish specific tasks. You are optimized for reliable tool calling, API interactions, and structured data processing.

        ~~ CAPABILITIES: ~~
        - Execute social media posting via Ayrshare API
        - Perform data processing and transformation
        - Make API calls to external services
        - Handle file operations and data management
        - Process structured data and JSON
        - Execute batch operations efficiently

        ~~ INSTRUCTIONS: ~~
        - Always use the appropriate tool for each task
        - Handle errors gracefully and provide clear feedback
        - Validate inputs before making API calls
        - Return structured, actionable results
        - Be efficient and minimize unnecessary API calls
        - Log important actions and results
        """
        
        try:
            self.agent = Agent(
                get_smart_model(),
                system_prompt=system_prompt,
                deps_type=ToolWorkerDeps,
                instructions="You are a tool execution specialist. Execute functions accurately and efficiently.",
                retries=2
            )
            
            # Add tools to the agent
            self._add_agent_tools()
            
            logger.info("Tool worker agent initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize tool worker agent", error=str(e))
            self.agent = None
    
    def _add_agent_tools(self):
        """Add tools to the agent."""
        if not self.agent:
            return
        
        @self.agent.tool
        async def post_to_social_media(
            ctx: RunContext[ToolWorkerDeps],
            post_content: str,
            platforms: List[str],
            media_urls: Optional[List[str]] = None,
            schedule_date: Optional[str] = None,
            hashtags: Optional[List[str]] = None,
            mentions: Optional[List[str]] = None
        ) -> str:
            """
            Post content to social media platforms using Ayrshare.
            
            Args:
                ctx: Context object
                post_content: Text content to post
                platforms: List of platforms to post to
                media_urls: Optional media URLs
                schedule_date: Optional schedule date (ISO format)
                hashtags: Optional hashtags
                mentions: Optional mentions
                
            Returns:
                JSON string with posting results
            """
            try:
                if not ctx.deps.ayrshare_client:
                    return json.dumps({
                        "status": "error",
                        "message": "Ayrshare client not available"
                    })
                
                # Process hashtags and mentions into content
                final_content = post_content
                if hashtags:
                    final_content += " " + " ".join(hashtags)
                if mentions:
                    final_content += " " + " ".join(mentions)
                
                # Parse schedule date if provided
                parsed_schedule_date = None
                if schedule_date:
                    try:
                        parsed_schedule_date = datetime.fromisoformat(schedule_date.replace('Z', '+00:00'))
                    except ValueError:
                        return json.dumps({
                            "status": "error",
                            "message": f"Invalid schedule date format: {schedule_date}"
                        })
                
                # Make the API call
                result = await ctx.deps.ayrshare_client.post_to_social_media(
                    post_content=final_content,
                    platforms=platforms,
                    media_urls=media_urls,
                    schedule_date=parsed_schedule_date
                )
                
                return json.dumps(result)
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to post: {str(e)}"
                })
        
        @self.agent.tool
        async def get_social_media_analytics(
            ctx: RunContext[ToolWorkerDeps],
            post_id: str
        ) -> str:
            """
            Get analytics for a social media post.
            
            Args:
                ctx: Context object
                post_id: ID of the post to get analytics for
                
            Returns:
                JSON string with analytics data
            """
            try:
                if not ctx.deps.ayrshare_client:
                    return json.dumps({
                        "status": "error",
                        "message": "Ayrshare client not available"
                    })
                
                result = await ctx.deps.ayrshare_client.get_post_analytics(post_id)
                return json.dumps(result)
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to get analytics: {str(e)}"
                })
        
        @self.agent.tool
        async def process_data(
            ctx: RunContext[ToolWorkerDeps],
            data: Dict[str, Any],
            operation: str,
            parameters: Optional[Dict[str, Any]] = None
        ) -> str:
            """
            Process data with specified operation.
            
            Args:
                ctx: Context object
                data: Data to process
                operation: Operation to perform
                parameters: Optional operation parameters
                
            Returns:
                JSON string with processed data
            """
            try:
                if operation == "filter":
                    # Filter data based on criteria
                    criteria = parameters.get("criteria", {}) if parameters else {}
                    filtered_data = {k: v for k, v in data.items() if self._matches_criteria(v, criteria)}
                    return json.dumps({"status": "success", "result": filtered_data})
                
                elif operation == "transform":
                    # Transform data structure
                    transformation = parameters.get("transformation", "identity") if parameters else "identity"
                    transformed_data = self._transform_data(data, transformation)
                    return json.dumps({"status": "success", "result": transformed_data})
                
                elif operation == "aggregate":
                    # Aggregate data
                    aggregation = parameters.get("aggregation", "count") if parameters else "count"
                    aggregated_data = self._aggregate_data(data, aggregation)
                    return json.dumps({"status": "success", "result": aggregated_data})
                
                else:
                    return json.dumps({
                        "status": "error",
                        "message": f"Unknown operation: {operation}"
                    })
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Data processing failed: {str(e)}"
                })
        
        @self.agent.tool
        async def validate_content(
            ctx: RunContext[ToolWorkerDeps],
            content: str,
            platform: str,
            validation_rules: Optional[Dict[str, Any]] = None
        ) -> str:
            """
            Validate content for a specific platform.
            
            Args:
                ctx: Context object
                content: Content to validate
                platform: Target platform
                validation_rules: Optional custom validation rules
                
            Returns:
                JSON string with validation results
            """
            try:
                validation_result = {
                    "is_valid": True,
                    "warnings": [],
                    "errors": [],
                    "suggestions": []
                }
                
                # Platform-specific validation
                if platform.lower() == "twitter":
                    if len(content) > 280:
                        validation_result["errors"].append("Content exceeds Twitter's 280 character limit")
                        validation_result["is_valid"] = False
                
                elif platform.lower() == "instagram":
                    if len(content) > 2200:
                        validation_result["errors"].append("Content exceeds Instagram's 2200 character limit")
                        validation_result["is_valid"] = False
                    
                    hashtag_count = content.count('#')
                    if hashtag_count > 30:
                        validation_result["warnings"].append("Instagram recommends using no more than 30 hashtags")
                
                elif platform.lower() == "linkedin":
                    if len(content) > 3000:
                        validation_result["errors"].append("Content exceeds LinkedIn's 3000 character limit")
                        validation_result["is_valid"] = False
                
                # Custom validation rules
                if validation_rules:
                    for rule, value in validation_rules.items():
                        if rule == "max_hashtags" and content.count('#') > value:
                            validation_result["warnings"].append(f"Content has more than {value} hashtags")
                        elif rule == "required_keywords":
                            missing_keywords = [kw for kw in value if kw.lower() not in content.lower()]
                            if missing_keywords:
                                validation_result["suggestions"].append(f"Consider including: {', '.join(missing_keywords)}")
                
                return json.dumps(validation_result)
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Content validation failed: {str(e)}"
                })
    
    def _matches_criteria(self, value: Any, criteria: Dict[str, Any]) -> bool:
        """Check if a value matches the given criteria."""
        for key, expected in criteria.items():
            if isinstance(value, dict) and key in value:
                if value[key] != expected:
                    return False
            elif hasattr(value, key):
                if getattr(value, key) != expected:
                    return False
        return True
    
    def _transform_data(self, data: Dict[str, Any], transformation: str) -> Dict[str, Any]:
        """Transform data based on the specified transformation."""
        if transformation == "identity":
            return data
        elif transformation == "lowercase_keys":
            return {k.lower(): v for k, v in data.items()}
        elif transformation == "uppercase_keys":
            return {k.upper(): v for k, v in data.items()}
        else:
            return data
    
    def _aggregate_data(self, data: Dict[str, Any], aggregation: str) -> Dict[str, Any]:
        """Aggregate data based on the specified aggregation method."""
        if aggregation == "count":
            return {"count": len(data)}
        elif aggregation == "keys":
            return {"keys": list(data.keys())}
        elif aggregation == "values":
            return {"values": list(data.values())}
        else:
            return {"result": "unknown_aggregation"}
    
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process a tool execution task using GPT-5 Mini.
        
        Args:
            task: Tool execution task
            
        Returns:
            WorkerResult with execution results
        """
        if not self.agent:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message="GPT-5 Mini agent not initialized"
            )
        
        try:
            # Extract task parameters
            tool_name = task.input_data.get("tool_name", "")
            prompt = task.input_data.get("prompt", "")
            parameters = task.input_data.get("parameters", {})
            
            if not prompt:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message="No prompt provided for tool execution"
                )
            
            # Create dependencies
            deps = ToolWorkerDeps(
                context=f"Executing tool: {tool_name}",
                available_tools=list(self.available_tools.keys()),
                ayrshare_client=self.ayrshare_client,
                workspace_id=task.workspace_id,
                user_id=task.user_id
            )
            
            # Run the agent
            result = await self.agent.run(prompt, deps=deps)
            
            # Extract the execution result
            if hasattr(result, 'data') and result.data:
                execution_result = result.data
            else:
                execution_result = str(result.output)
            
            tool_result = {
                "tool_name": tool_name,
                "execution_result": execution_result,
                "parameters": parameters,
                "model_used": self.model,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Tool execution task completed successfully",
                task_id=task.task_id,
                tool_name=tool_name,
                result_length=len(str(execution_result))
            )
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="success",
                result=tool_result,
                metadata={
                    "model": self.model,
                    "tool_name": tool_name,
                    "result_length": len(str(execution_result))
                }
            )
            
        except Exception as e:
            logger.error("Tool execution task failed", task_id=task.task_id, error=str(e))
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Tool execution failed: {str(e)}"
            )
    
    async def health_check(self) -> bool:
        """Check if GPT-5 Mini agent is working."""
        if not self.agent:
            self.is_healthy = False
            return False
        
        try:
            # Simple test task
            test_deps = ToolWorkerDeps(
                context="Health check test",
                available_tools=list(self.available_tools.keys())
            )
            result = await self.agent.run("Perform a health check", deps=test_deps)
            
            self.is_healthy = bool(result)
            self.last_health_check = datetime.utcnow()
            
            return self.is_healthy
            
        except Exception as e:
            logger.warning("Tool worker health check failed", error=str(e))
            self.is_healthy = False
            self.last_health_check = datetime.utcnow()
            return False