#!/usr/bin/env python3
"""
Configuration Validation Script
Validates environment configuration and provides helpful feedback.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import structlog

from core.env_config import AppConfig, Environment, get_config

# Configure simple logging for this script
structlog.configure(
    processors=[structlog.dev.ConsoleRenderer(colors=True)],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def print_header():
    """Print script header."""
    print("=" * 70)
    print("🔧 AI Social Media Platform - Configuration Validator")
    print("=" * 70)
    print()


def print_section(title: str):
    """Print section header."""
    print(f"\n📋 {title}")
    print("-" * 50)


def print_status(item: str, status: bool, details: str = ""):
    """Print status with emoji."""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {item}")
    if details:
        print(f"   {details}")


def print_warning(message: str):
    """Print warning message."""
    print(f"⚠️  {message}")


def print_info(message: str):
    """Print info message."""
    print(f"💡 {message}")


def validate_environment_file():
    """Check if .env file exists."""
    env_file = backend_dir / ".env"
    if env_file.exists():
        print_status(".env file", True, f"Found at {env_file}")
        return True
    else:
        print_status(".env file", False, "Not found - copy from env.template")
        return False


def validate_configuration():
    """Validate the configuration."""
    try:
        config = get_config()
        validation_result = config.validate()

        print_section("Configuration Status")
        print_status("Configuration loaded", True)
        print_status("Configuration valid", validation_result["valid"])

        if validation_result["errors"]:
            print("\n❌ Configuration Errors:")
            for error in validation_result["errors"]:
                print(f"   • {error}")

        if validation_result["warnings"]:
            print("\n⚠️  Configuration Warnings:")
            for warning in validation_result["warnings"]:
                print(f"   • {warning}")

        return config, validation_result

    except Exception as e:
        print_status("Configuration loaded", False, str(e))
        return None, None


def validate_providers(config: AppConfig, validation_result: Dict[str, Any]):
    """Validate AI providers."""
    print_section("AI Providers")

    providers = validation_result["providers"]

    # Database (required)
    print_status("Database (Supabase)", providers["database"])

    # Primary AI providers
    primary_providers = ["openai", "anthropic"]
    primary_count = sum(1 for p in primary_providers if providers.get(p, False))

    print_status(
        "Primary AI Providers",
        primary_count > 0,
        f"{primary_count}/2 configured (OpenAI: {providers.get('openai', False)}, Anthropic: {providers.get('anthropic', False)})",
    )

    # Secondary providers
    secondary_providers = [
        ("perplexity", "Perplexity (Research)"),
        ("gemini", "Google Gemini (Advanced AI)"),
        ("heygen", "HeyGen (Avatar Videos)"),
        ("midjourney", "Midjourney (Images)"),
        ("ayrshare", "Ayrshare (Social Media)"),
    ]

    for key, name in secondary_providers:
        print_status(name, providers.get(key, False))


def validate_environment_specific(config: AppConfig):
    """Validate environment-specific requirements."""
    print_section(f"Environment: {config.server.environment.value.title()}")

    if config.server.environment == Environment.PRODUCTION:
        print_status("JWT Secret", bool(config.server.jwt_secret))
        print_status("CORS Origins", len(config.server.cors_origins) > 0)

        # Check for production-ready AI providers
        has_primary = bool(config.ai_providers.openai_api_key or config.ai_providers.anthropic_api_key)
        print_status("Primary AI Provider", has_primary)

    elif config.server.environment == Environment.DEVELOPMENT:
        print_info("Development environment - relaxed validation")
        print_status("Server Host", config.server.host == "0.0.0.0")
        print_status("Server Port", config.server.port == 8000)


def provide_recommendations(config: AppConfig, validation_result: Dict[str, Any]):
    """Provide configuration recommendations."""
    print_section("Recommendations")

    if not validation_result["valid"]:
        print_warning("Fix configuration errors before deploying to production")

    providers = validation_result["providers"]

    # Missing providers recommendations
    if not providers.get("ayrshare"):
        print_info("Add AYRSHARE_API_KEY to enable social media posting")

    if not providers.get("heygen"):
        print_info("Add HEYGEN_API_KEY to enable avatar video generation")

    if not providers.get("midjourney"):
        print_info("Add COMETAPI_KEY to enable Midjourney image generation")

    if not providers.get("perplexity"):
        print_info("Add PERPLEXITY_API_KEY to enhance research capabilities")

    # Environment-specific recommendations
    if config.server.environment == Environment.DEVELOPMENT:
        print_info("Consider setting up production environment variables")

    if config.server.environment == Environment.PRODUCTION:
        if not config.server.jwt_secret:
            print_warning("Set JWT_SECRET for production security")


def generate_config_report(config: AppConfig, validation_result: Dict[str, Any]):
    """Generate a configuration report."""
    report = {
        "timestamp": "2025-08-17T19:30:00Z",
        "environment": config.server.environment.value,
        "valid": validation_result["valid"],
        "providers": validation_result["providers"],
        "server": {
            "host": config.server.host,
            "port": config.server.port,
            "log_level": config.server.log_level.value,
            "cors_origins_count": len(config.server.cors_origins),
        },
        "security": {"jwt_secret_configured": bool(config.server.jwt_secret)},
    }

    report_file = backend_dir / "config_validation_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print_section("Report Generated")
    print_status("Configuration report", True, f"Saved to {report_file}")


def main():
    """Main validation function."""
    print_header()

    # Check environment file
    env_exists = validate_environment_file()

    if not env_exists:
        print("\n❌ Cannot proceed without .env file")
        print("💡 Copy env.template to .env and fill in your values")
        return False

    # Validate configuration
    config, validation_result = validate_configuration()

    if config is None:
        print("\n❌ Cannot proceed with invalid configuration")
        return False

    # Detailed validation
    validate_providers(config, validation_result)
    validate_environment_specific(config)
    provide_recommendations(config, validation_result)

    # Generate report
    generate_config_report(config, validation_result)

    # Final status
    print_section("Final Status")
    if validation_result["valid"]:
        print("✅ Configuration is valid and ready for use!")
        return True
    else:
        print("❌ Configuration has issues that need to be resolved")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
