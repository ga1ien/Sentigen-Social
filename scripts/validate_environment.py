#!/usr/bin/env python3
"""
Environment Configuration Validator
Validates that all required environment variables are properly configured
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json

# Add the backend to the path
backend_path = Path(__file__).parent.parent / "social-media-module" / "backend"
sys.path.insert(0, str(backend_path))

try:
    from core.env_config import get_config, AppConfig
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Error importing backend modules: {e}")
    print("Make sure you're running this from the project root and backend dependencies are installed")
    sys.exit(1)


class EnvironmentValidator:
    """Validates environment configuration."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate_file_exists(self, file_path: str) -> bool:
        """Check if environment file exists."""
        if not os.path.exists(file_path):
            self.errors.append(f"Environment file not found: {file_path}")
            return False
        self.info.append(f"✅ Found environment file: {file_path}")
        return True

    def validate_backend_config(self) -> Dict[str, Any]:
        """Validate backend configuration."""
        try:
            config = get_config()
            status = config.validate()

            if status["valid"]:
                self.info.append("✅ Backend configuration is valid")
            else:
                self.errors.extend([f"Backend: {error}" for error in status["errors"]])

            # Check provider availability
            providers = status["providers"]
            available_providers = [name for name, available in providers.items() if available]
            unavailable_providers = [name for name, available in providers.items() if not available]

            if available_providers:
                self.info.append(f"✅ Available services: {', '.join(available_providers)}")

            if unavailable_providers:
                self.warnings.append(f"⚠️ Unavailable services: {', '.join(unavailable_providers)}")

            return status

        except Exception as e:
            self.errors.append(f"Backend configuration error: {str(e)}")
            return {"valid": False, "error": str(e)}

    def validate_frontend_env(self) -> bool:
        """Validate frontend environment variables."""
        frontend_vars = [
            "NEXT_PUBLIC_SUPABASE_URL",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_API_URL"
        ]

        missing_vars = []
        for var in frontend_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            self.warnings.append(f"⚠️ Missing frontend variables: {', '.join(missing_vars)}")
            self.info.append("💡 Copy NEXT_PUBLIC_* variables to frontend/.env.local")
            return False
        else:
            self.info.append("✅ Frontend environment variables are set")
            return True

    def validate_security(self) -> bool:
        """Validate security configuration."""
        jwt_secret = os.getenv("JWT_SECRET")
        app_env = os.getenv("APP_ENV", "development")

        if not jwt_secret:
            if app_env == "production":
                self.errors.append("❌ JWT_SECRET is required for production")
                return False
            else:
                self.warnings.append("⚠️ JWT_SECRET not set (required for production)")
        elif len(jwt_secret) < 32:
            self.warnings.append("⚠️ JWT_SECRET should be at least 32 characters")
        else:
            self.info.append("✅ JWT_SECRET is properly configured")

        # Check CORS configuration
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if app_env == "production" and "localhost" in cors_origins:
            self.warnings.append("⚠️ Production CORS includes localhost - update for production")

        return True

    def validate_ai_providers(self) -> Tuple[List[str], List[str]]:
        """Validate AI provider configuration."""
        providers = {
            "OpenAI": os.getenv("OPENAI_API_KEY"),
            "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "Perplexity": os.getenv("PERPLEXITY_API_KEY"),
            "Gemini": os.getenv("GEMINI_API_KEY"),
            "HeyGen": os.getenv("HEYGEN_API_KEY"),
            "Midjourney": os.getenv("COMETAPI_KEY")
        }

        available = [name for name, key in providers.items() if key]
        missing = [name for name, key in providers.items() if not key]

        primary_providers = ["OpenAI", "Anthropic"]
        has_primary = any(providers[p] for p in primary_providers)

        if not has_primary:
            self.errors.append("❌ At least one primary AI provider (OpenAI/Anthropic) is required")

        if available:
            self.info.append(f"✅ Available AI providers: {', '.join(available)}")

        if missing:
            self.info.append(f"💡 Optional providers not configured: {', '.join(missing)}")

        return available, missing

    def validate_database(self) -> bool:
        """Validate database configuration."""
        required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_ANON_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            self.errors.append(f"❌ Missing database variables: {', '.join(missing_vars)}")
            return False

        # Validate URL format
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url.startswith("https://"):
            self.errors.append("❌ SUPABASE_URL must start with https://")
            return False

        # Validate key formats
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        anon_key = os.getenv("SUPABASE_ANON_KEY")

        if not service_key.startswith("eyJ"):
            self.warnings.append("⚠️ SUPABASE_SERVICE_KEY format looks incorrect")

        if not anon_key.startswith("eyJ"):
            self.warnings.append("⚠️ SUPABASE_ANON_KEY format looks incorrect")

        self.info.append("✅ Database configuration looks good")
        return True

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "summary": {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings),
                "status": "✅ VALID" if len(self.errors) == 0 else "❌ INVALID"
            }
        }


def main():
    """Main validation function."""
    print("🔍 Validating Environment Configuration...")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    validator = EnvironmentValidator()

    # Check if environment file exists
    env_files = [".env", "env.unified.template"]
    env_file_exists = any(validator.validate_file_exists(f) for f in env_files)

    if not env_file_exists:
        print("\n❌ No environment file found!")
        print("💡 Copy env.unified.template to .env and configure your values")
        sys.exit(1)

    # Validate different aspects
    print("\n🗄️ Validating Database Configuration...")
    validator.validate_database()

    print("\n🤖 Validating AI Providers...")
    validator.validate_ai_providers()

    print("\n🔐 Validating Security Configuration...")
    validator.validate_security()

    print("\n🎨 Validating Frontend Configuration...")
    validator.validate_frontend_env()

    print("\n⚙️ Validating Backend Configuration...")
    validator.validate_backend_config()

    # Generate and display report
    report = validator.generate_report()

    print("\n" + "=" * 50)
    print("📊 VALIDATION REPORT")
    print("=" * 50)

    # Display info messages
    if report["info"]:
        for info in report["info"]:
            print(info)

    # Display warnings
    if report["warnings"]:
        print("\n⚠️ WARNINGS:")
        for warning in report["warnings"]:
            print(f"  {warning}")

    # Display errors
    if report["errors"]:
        print("\n❌ ERRORS:")
        for error in report["errors"]:
            print(f"  {error}")

    # Display summary
    print(f"\n📋 SUMMARY: {report['summary']['status']}")
    print(f"   Errors: {report['summary']['total_errors']}")
    print(f"   Warnings: {report['summary']['total_warnings']}")

    if report["valid"]:
        print("\n🎉 Environment configuration is valid!")
        print("💡 Your application should start successfully")
    else:
        print("\n🚨 Environment configuration has errors!")
        print("💡 Fix the errors above before starting the application")
        sys.exit(1)

    # Save report to file
    report_file = "config_validation_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📄 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
