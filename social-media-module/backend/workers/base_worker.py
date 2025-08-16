"""
Base worker class for all specialized AI workers.
"""

import os
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import structlog
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger(__name__)


@dataclass
class WorkerTask:
    """Base task structure for all workers."""
    task_id: str
    task_type: str
    input_data: Dict[str, Any]
    priority: int = 1
    created_at: datetime = None
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class WorkerResult:
    """Base result structure for all workers."""
    task_id: str
    worker_type: str
    status: str  # "success", "error", "partial"
    result: Any
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class BaseWorker(ABC):
    """Base class for all specialized AI workers."""
    
    def __init__(self, worker_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base worker.
        
        Args:
            worker_name: Name of the worker
            config: Optional configuration dictionary
        """
        self.worker_name = worker_name
        self.config = config or {}
        self.is_healthy = False
        self.last_health_check = None
        
        # Initialize worker-specific configuration
        self._initialize_config()
        
        logger.info(f"Initialized {worker_name} worker")
    
    @abstractmethod
    def _initialize_config(self):
        """Initialize worker-specific configuration."""
        pass
    
    @abstractmethod
    async def process_task(self, task: WorkerTask) -> WorkerResult:
        """
        Process a task and return the result.
        
        Args:
            task: The task to process
            
        Returns:
            WorkerResult with the processing results
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the worker is healthy and ready to process tasks.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    async def execute_with_timeout(self, task: WorkerTask, timeout: int = 300) -> WorkerResult:
        """
        Execute a task with timeout protection.
        
        Args:
            task: The task to execute
            timeout: Timeout in seconds
            
        Returns:
            WorkerResult with execution results
        """
        start_time = datetime.utcnow()
        
        try:
            result = await asyncio.wait_for(
                self.process_task(task),
                timeout=timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            logger.info(
                f"Task completed successfully",
                worker=self.worker_name,
                task_id=task.task_id,
                execution_time=execution_time
            )
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(
                f"Task timed out",
                worker=self.worker_name,
                task_id=task.task_id,
                timeout=timeout
            )
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=f"Task timed out after {timeout} seconds",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(
                f"Task failed with error",
                worker=self.worker_name,
                task_id=task.task_id,
                error=str(e)
            )
            
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_name,
                status="error",
                result=None,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def batch_process(self, tasks: List[WorkerTask]) -> List[WorkerResult]:
        """
        Process multiple tasks concurrently.
        
        Args:
            tasks: List of tasks to process
            
        Returns:
            List of WorkerResults
        """
        logger.info(
            f"Processing batch of tasks",
            worker=self.worker_name,
            task_count=len(tasks)
        )
        
        # Process tasks concurrently
        results = await asyncio.gather(
            *[self.execute_with_timeout(task) for task in tasks],
            return_exceptions=True
        )
        
        # Handle any exceptions that occurred
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(WorkerResult(
                    task_id=tasks[i].task_id,
                    worker_type=self.worker_name,
                    status="error",
                    result=None,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the worker.
        
        Returns:
            Dictionary with worker status information
        """
        return {
            "worker_name": self.worker_name,
            "is_healthy": self.is_healthy,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "config": {k: "***" if "key" in k.lower() or "password" in k.lower() else v 
                      for k, v in self.config.items()}
        }