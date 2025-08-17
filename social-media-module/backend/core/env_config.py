"""
Environment configuration and validation for the backend.
Provides type-safe environment variable access with validation.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str
    service_key: str
    anon_key: str

    def __post_init__(self):
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("SUPABASE_URL must be a valid URL")
        if not self.service_key.startswith("eyJ"):
            raise ValueError("SUPABASE_SERVICE_KEY appears to be invalid")
        if not self.anon_key.startswith("eyJ"):
            raise ValueError("SUPABASE_ANON_KEY appears to be invalid")


@dataclass
class AIProviderConfig:
    """AI provider configuration."""

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_org_id: Optional[str] = None

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    perplexity_api_key: Optional[str] = None
    perplexity_model: str = "llama-3.1-sonar-small-128k-online"

    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash-exp"

    heygen_api_key: Optional[str] = None
    heygen_base_url: str = "https://api.heygen.com/v2"

    cometapi_key: Optional[str] = None
    cometapi_base_url: str = "https://api.cometapi.com"

    def __post_init__(self):
        # Validate at least one AI provider is configured
        providers = [self.openai_api_key, self.anthropic_api_key, self.perplexity_api_key, self.gemini_api_key]
        if not any(providers):
            logger.warning("No AI providers configured - some features may not work")


@dataclass
class SocialMediaConfig:
    """Social media integration configuration."""

    ayrshare_api_key: Optional[str] = None
    ayrshare_base_url: str = "https://app.ayrshare.com/api"

    def __post_init__(self):
        if not self.ayrshare_api_key:
            logger.warning("Ayrshare not configured - social media posting disabled")


@dataclass
class ServerConfig:
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.INFO
    cors_origins: List[str] = None
    jwt_secret: Optional[str] = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = [
                "http://localhost:3000",
                "https://localhost:3000",
                "http://127.0.0.1:3000",
                "https://127.0.0.1:3000",
            ]

        if self.environment == Environment.PRODUCTION and not self.jwt_secret:
            logger.warning("JWT_SECRET not set in production environment")


@dataclass
class AppConfig:
    """Complete application configuration."""

    database: DatabaseConfig
    ai_providers: AIProviderConfig
    social_media: SocialMediaConfig
    server: ServerConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        load_dotenv()

        # Database config (required)
        database = DatabaseConfig(
            url=_get_required_env("SUPABASE_URL"),
            service_key=_get_required_env("SUPABASE_SERVICE_KEY"),
            anon_key=_get_required_env("SUPABASE_ANON_KEY"),
        )

        # AI providers config
        ai_providers = AIProviderConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4o"),
            openai_org_id=os.getenv("OPENAI_ORG_ID"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            anthropic_model=os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
            perplexity_model=os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GOOGLE_VEO3_MODEL", "gemini-2.0-flash-exp"),
            heygen_api_key=os.getenv("HEYGEN_API_KEY"),
            heygen_base_url=os.getenv("HEYGEN_BASE_URL", "https://api.heygen.com/v2"),
            cometapi_key=os.getenv("COMETAPI_KEY"),
            cometapi_base_url=os.getenv("COMETAPI_BASE_URL", "https://api.cometapi.com"),
        )

        # Social media config
        social_media = SocialMediaConfig(
            ayrshare_api_key=os.getenv("AYRSHARE_API_KEY"),
            ayrshare_base_url=os.getenv("AYRSHARE_BASE_URL", "https://app.ayrshare.com/api"),
        )

        # Server config
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        cors_origins = (
            [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()] if cors_origins_str else None
        )

        server = ServerConfig(
            host=os.getenv("APP_HOST", "0.0.0.0"),
            port=int(os.getenv("APP_PORT", "8000")),
            environment=Environment(os.getenv("APP_ENV", "development")),
            log_level=LogLevel(os.getenv("LOG_LEVEL", "info").lower().strip()),
            cors_origins=cors_origins,
            jwt_secret=os.getenv("JWT_SECRET"),
        )

        return cls(database=database, ai_providers=ai_providers, social_media=social_media, server=server)

    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return status."""
        status = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "providers": {
                "database": True,
                "openai": bool(self.ai_providers.openai_api_key),
                "anthropic": bool(self.ai_providers.anthropic_api_key),
                "perplexity": bool(self.ai_providers.perplexity_api_key),
                "gemini": bool(self.ai_providers.gemini_api_key),
                "heygen": bool(self.ai_providers.heygen_api_key),
                "midjourney": bool(self.ai_providers.cometapi_key),
                "ayrshare": bool(self.social_media.ayrshare_api_key),
            },
        }

        # Check for production-specific requirements
        if self.server.environment == Environment.PRODUCTION:
            if not self.server.jwt_secret:
                status["errors"].append("JWT_SECRET is required in production")
                status["valid"] = False

            if not any([self.ai_providers.openai_api_key, self.ai_providers.anthropic_api_key]):
                status["errors"].append("At least one primary AI provider (OpenAI/Anthropic) required in production")
                status["valid"] = False

        return status


def _get_required_env(key: str) -> str:
    """Get required environment variable or raise error."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


# Global configuration instance
config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = AppConfig.from_env()

        # Log configuration status
        status = config.validate()
        if status["valid"]:
            logger.info(
                "Configuration loaded successfully",
                environment=config.server.environment.value,
                providers=status["providers"],
            )
        else:
            logger.error("Configuration validation failed", errors=status["errors"])
            raise ValueError(f"Configuration errors: {status['errors']}")

    return config


def reload_config() -> AppConfig:
    """Reload configuration from environment."""
    global config
    config = None
    return get_config()
