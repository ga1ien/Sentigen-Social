"""
API response optimization utilities.
Provides response compression, pagination, and performance monitoring.
"""

import gzip
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import structlog
from fastapi import Response
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


@dataclass
class PaginationParams:
    """Pagination parameters."""

    page: int = 1
    per_page: int = 20
    max_per_page: int = 100

    def __post_init__(self):
        self.page = max(1, self.page)
        self.per_page = min(max(1, self.per_page), self.max_per_page)

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.per_page


@dataclass
class PaginatedResponse:
    """Paginated response structure."""

    data: List[Any]
    pagination: Dict[str, Any]

    @classmethod
    def create(cls, data: List[Any], total_count: int, params: PaginationParams) -> "PaginatedResponse":
        """Create paginated response."""
        total_pages = (total_count + params.per_page - 1) // params.per_page

        pagination = {
            "current_page": params.page,
            "per_page": params.per_page,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": params.page < total_pages,
            "has_prev": params.page > 1,
            "next_page": params.page + 1 if params.page < total_pages else None,
            "prev_page": params.page - 1 if params.page > 1 else None,
        }

        return cls(data=data, pagination=pagination)


class ResponseOptimizer:
    """Optimize API responses for performance."""

    def __init__(self):
        self.compression_threshold = 1024  # Compress responses larger than 1KB
        self.enable_compression = True
        self.response_stats = {
            "total_responses": 0,
            "compressed_responses": 0,
            "avg_response_size": 0.0,
            "compression_ratio": 0.0,
        }

    def optimize_response(
        self, data: Any, compress: bool = True, exclude_fields: Optional[List[str]] = None
    ) -> JSONResponse:
        """Optimize API response with compression and field filtering."""

        # Filter out excluded fields
        if exclude_fields and isinstance(data, dict):
            data = {k: v for k, v in data.items() if k not in exclude_fields}
        elif exclude_fields and isinstance(data, list):
            data = [
                {k: v for k, v in item.items() if k not in exclude_fields} if isinstance(item, dict) else item
                for item in data
            ]

        # Serialize to JSON
        json_str = json.dumps(data, default=self._json_serializer, ensure_ascii=False)
        original_size = len(json_str.encode("utf-8"))

        # Update stats
        self.response_stats["total_responses"] += 1

        # Compress if enabled and size exceeds threshold
        if compress and self.enable_compression and original_size > self.compression_threshold:
            compressed_data = gzip.compress(json_str.encode("utf-8"))
            compression_ratio = len(compressed_data) / original_size

            # Only use compression if it actually reduces size significantly
            if compression_ratio < 0.9:
                self.response_stats["compressed_responses"] += 1
                self._update_compression_stats(original_size, len(compressed_data))

                return Response(
                    content=compressed_data, media_type="application/json", headers={"Content-Encoding": "gzip"}
                )

        # Return uncompressed response
        self._update_response_stats(original_size)
        return JSONResponse(content=data)

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for common types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "dict"):  # Pydantic models
            return obj.dict()
        elif hasattr(obj, "__dict__"):  # Regular objects
            return obj.__dict__
        else:
            return str(obj)

    def _update_compression_stats(self, original_size: int, compressed_size: int):
        """Update compression statistics."""
        compression_ratio = compressed_size / original_size

        # Update running averages
        total = self.response_stats["total_responses"]
        self.response_stats["avg_response_size"] = (
            self.response_stats["avg_response_size"] * (total - 1) + original_size
        ) / total

        compressed_total = self.response_stats["compressed_responses"]
        self.response_stats["compression_ratio"] = (
            self.response_stats["compression_ratio"] * (compressed_total - 1) + compression_ratio
        ) / compressed_total

    def _update_response_stats(self, size: int):
        """Update response statistics."""
        total = self.response_stats["total_responses"]
        self.response_stats["avg_response_size"] = (
            self.response_stats["avg_response_size"] * (total - 1) + size
        ) / total

    def get_stats(self) -> Dict[str, Any]:
        """Get response optimization statistics."""
        total = self.response_stats["total_responses"]
        compressed = self.response_stats["compressed_responses"]

        return {
            **self.response_stats,
            "compression_percentage": (compressed / total * 100) if total > 0 else 0,
            "avg_compression_ratio": self.response_stats["compression_ratio"],
        }


class FieldSelector:
    """Optimize responses by selecting only requested fields."""

    @staticmethod
    def select_fields(data: Any, fields: Optional[List[str]] = None) -> Any:
        """Select only specified fields from response data."""
        if not fields:
            return data

        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k in fields}
        elif isinstance(data, list):
            return [FieldSelector.select_fields(item, fields) for item in data]
        else:
            return data

    @staticmethod
    def exclude_fields(data: Any, exclude: Optional[List[str]] = None) -> Any:
        """Exclude specified fields from response data."""
        if not exclude:
            return data

        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k not in exclude}
        elif isinstance(data, list):
            return [FieldSelector.exclude_fields(item, exclude) for item in data]
        else:
            return data


class ResponseCache:
    """Cache optimized responses."""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.access_order: List[str] = []

    def get(self, key: str) -> Optional[Any]:
        """Get cached response."""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)

            cache_entry = self.cache[key]
            if cache_entry["expires_at"] > datetime.utcnow():
                return cache_entry["data"]
            else:
                # Expired
                del self.cache[key]
                self.access_order.remove(key)

        return None

    def set(self, key: str, data: Any, ttl_seconds: int = 300):
        """Set cached response."""
        # Remove oldest entries if cache is full
        while len(self.cache) >= self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]

        self.cache[key] = {
            "data": data,
            "expires_at": datetime.utcnow().timestamp() + ttl_seconds,
            "created_at": datetime.utcnow(),
        }
        self.access_order.append(key)

    def clear(self):
        """Clear all cached responses."""
        self.cache.clear()
        self.access_order.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": 0.0,  # Would need to track hits/misses
        }


# Global instances
response_optimizer = ResponseOptimizer()
response_cache = ResponseCache()


def get_response_optimizer() -> ResponseOptimizer:
    """Get the global response optimizer."""
    return response_optimizer


def get_response_cache() -> ResponseCache:
    """Get the global response cache."""
    return response_cache
