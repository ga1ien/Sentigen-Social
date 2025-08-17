"""
Database query optimization utilities.
Provides connection pooling, query caching, and performance monitoring.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class QueryStats:
    """Query performance statistics."""

    query_hash: str
    execution_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    last_executed: Optional[datetime] = None
    slow_query_threshold: float = 1.0  # seconds


@dataclass
class DatabaseOptimizer:
    """Database performance optimizer."""

    query_stats: Dict[str, QueryStats] = field(default_factory=dict)
    slow_query_threshold: float = 1.0
    enable_query_logging: bool = True
    enable_performance_monitoring: bool = True

    def track_query_performance(self, func: Callable):
        """Decorator to track query performance."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not self.enable_performance_monitoring:
                return await func(*args, **kwargs)

            # Generate query identifier
            query_hash = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Update statistics
                self._update_query_stats(query_hash, execution_time, func.__name__)

                # Log slow queries
                if execution_time > self.slow_query_threshold:
                    logger.warning(
                        "Slow query detected",
                        function=func.__name__,
                        execution_time=execution_time,
                        args_count=len(args),
                        kwargs_count=len(kwargs),
                    )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error("Query failed", function=func.__name__, execution_time=execution_time, error=str(e))
                raise

        return wrapper

    def _update_query_stats(self, query_hash: str, execution_time: float, function_name: str):
        """Update query statistics."""
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = QueryStats(
                query_hash=query_hash, slow_query_threshold=self.slow_query_threshold
            )

        stats = self.query_stats[query_hash]
        stats.execution_count += 1
        stats.total_time += execution_time
        stats.avg_time = stats.total_time / stats.execution_count
        stats.min_time = min(stats.min_time, execution_time)
        stats.max_time = max(stats.max_time, execution_time)
        stats.last_executed = datetime.utcnow()

        if self.enable_query_logging and stats.execution_count % 100 == 0:
            logger.info(
                "Query performance update",
                function=function_name,
                execution_count=stats.execution_count,
                avg_time=stats.avg_time,
                max_time=stats.max_time,
            )

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        total_queries = sum(stats.execution_count for stats in self.query_stats.values())
        slow_queries = [stats for stats in self.query_stats.values() if stats.avg_time > self.slow_query_threshold]

        # Top 10 slowest queries by average time
        slowest_queries = sorted(self.query_stats.values(), key=lambda x: x.avg_time, reverse=True)[:10]

        # Most frequently executed queries
        frequent_queries = sorted(self.query_stats.values(), key=lambda x: x.execution_count, reverse=True)[:10]

        return {
            "summary": {
                "total_queries": total_queries,
                "unique_queries": len(self.query_stats),
                "slow_queries_count": len(slow_queries),
                "avg_execution_time": sum(stats.avg_time for stats in self.query_stats.values()) / len(self.query_stats)
                if self.query_stats
                else 0,
            },
            "slowest_queries": [
                {
                    "query_hash": stats.query_hash,
                    "avg_time": stats.avg_time,
                    "max_time": stats.max_time,
                    "execution_count": stats.execution_count,
                }
                for stats in slowest_queries
            ],
            "most_frequent_queries": [
                {
                    "query_hash": stats.query_hash,
                    "execution_count": stats.execution_count,
                    "avg_time": stats.avg_time,
                    "total_time": stats.total_time,
                }
                for stats in frequent_queries
            ],
        }

    def optimize_suggestions(self) -> List[str]:
        """Generate optimization suggestions."""
        suggestions = []

        # Check for slow queries
        slow_queries = [stats for stats in self.query_stats.values() if stats.avg_time > self.slow_query_threshold]

        if slow_queries:
            suggestions.append(
                f"Found {len(slow_queries)} slow queries. Consider adding database indexes or optimizing query logic."
            )

        # Check for frequently executed queries
        frequent_queries = [stats for stats in self.query_stats.values() if stats.execution_count > 1000]

        if frequent_queries:
            suggestions.append(
                f"Found {len(frequent_queries)} frequently executed queries. Consider implementing caching."
            )

        # Check for queries with high variance in execution time
        variable_queries = [
            stats
            for stats in self.query_stats.values()
            if stats.max_time > stats.avg_time * 3 and stats.execution_count > 10
        ]

        if variable_queries:
            suggestions.append(
                f"Found {len(variable_queries)} queries with inconsistent performance. Check for resource contention."
            )

        return suggestions


class ConnectionPoolOptimizer:
    """Optimize database connection pooling."""

    def __init__(self):
        self.connection_stats = {
            "active_connections": 0,
            "total_connections_created": 0,
            "connection_errors": 0,
            "avg_connection_time": 0.0,
        }

    def get_optimal_pool_size(self, concurrent_users: int = 100) -> Dict[str, int]:
        """Calculate optimal connection pool size."""
        # Rule of thumb: pool size should be roughly equal to the number of CPU cores
        # for CPU-bound operations, but can be higher for I/O-bound operations

        import os

        cpu_cores = os.cpu_count() or 4

        # Base pool size on CPU cores and expected concurrent users
        min_size = max(2, cpu_cores // 2)
        max_size = min(50, cpu_cores * 2 + (concurrent_users // 10))

        return {"min_size": min_size, "max_size": max_size, "recommended_size": min(20, cpu_cores * 2)}

    def monitor_connection_health(self) -> Dict[str, Any]:
        """Monitor connection pool health."""
        return {"stats": self.connection_stats, "recommendations": self._get_connection_recommendations()}

    def _get_connection_recommendations(self) -> List[str]:
        """Get connection pool recommendations."""
        recommendations = []

        if self.connection_stats["connection_errors"] > 10:
            recommendations.append("High connection error rate detected. Check database connectivity.")

        if self.connection_stats["avg_connection_time"] > 5.0:
            recommendations.append("Slow connection times detected. Consider connection pooling optimization.")

        return recommendations


# Global optimizer instance
db_optimizer = DatabaseOptimizer()
connection_optimizer = ConnectionPoolOptimizer()


def get_db_optimizer() -> DatabaseOptimizer:
    """Get the global database optimizer."""
    return db_optimizer


def get_connection_optimizer() -> ConnectionPoolOptimizer:
    """Get the global connection optimizer."""
    return connection_optimizer


# Decorator for easy use
def monitor_query_performance(func: Callable):
    """Decorator to monitor query performance."""
    return db_optimizer.track_query_performance(func)
