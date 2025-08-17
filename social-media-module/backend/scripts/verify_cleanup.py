#!/usr/bin/env python3
"""
Verification script for social-media-module cleanup
Checks that all deprecated code has been removed and core functionality works
"""

import importlib.util
import os
import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    return Path(filepath).exists()


def check_directory_exists(dirpath: str) -> bool:
    """Check if a directory exists"""
    return Path(dirpath).is_dir()


def verify_deprecated_removal():
    """Verify that deprecated files and directories have been removed"""
    print("🔍 Verifying deprecated code removal...")

    deprecated_items = [
        # Deprecated directories
        "features/archive/",
        "scrapers/",
        # Deprecated files
        "api/content_research_orchestrator.py",
        "api/routes/content_intelligence.py",
        "services/content_intelligence_orchestrator.py",
        # Deprecated configs
        "env.example",
        "Procfile",
        "nixpacks.toml",
    ]

    all_removed = True
    for item in deprecated_items:
        if check_file_exists(item) or check_directory_exists(item):
            print(f"❌ FAILED: {item} still exists")
            all_removed = False
        else:
            print(f"✅ REMOVED: {item}")

    return all_removed


def verify_core_files():
    """Verify that core files still exist and are functional"""
    print("\n🔍 Verifying core files...")

    core_files = [
        "api/main.py",
        "api/avatar_api.py",
        "api/unified_research_api.py",
        "core/env_config.py",
        "database/models.py",
        "database/consolidated_schema.sql",
        "config/production.env.template",
    ]

    all_exist = True
    for file in core_files:
        if check_file_exists(file):
            print(f"✅ EXISTS: {file}")
        else:
            print(f"❌ MISSING: {file}")
            all_exist = False

    return all_exist


def verify_imports():
    """Verify that key imports work correctly"""
    print("\n🔍 Verifying imports...")

    try:
        # Test core imports
        sys.path.append(str(Path(__file__).parent.parent))

        from core.env_config import get_config

        print("✅ IMPORT: core.env_config")

        from database.models import User, Workspace

        print("✅ IMPORT: database.models")

        # Test that Chrome MCP imports fail (as expected)
        try:
            from services.content_intelligence_orchestrator import ContentIntelligenceOrchestrator

            print("❌ UNEXPECTED: Chrome MCP import succeeded")
            return False
        except ImportError:
            print("✅ EXPECTED: Chrome MCP import failed (removed)")

        return True

    except Exception as e:
        print(f"❌ IMPORT ERROR: {e}")
        return False


def verify_database_schema():
    """Verify database schema file is properly formatted"""
    print("\n🔍 Verifying database schema...")

    schema_file = "database/consolidated_schema.sql"
    if not check_file_exists(schema_file):
        print(f"❌ MISSING: {schema_file}")
        return False

    with open(schema_file, "r") as f:
        content = f.read()

    # Check for key tables
    required_tables = [
        "users",
        "workspaces",
        "social_media_posts",
        "media_assets",
        "worker_tasks",
        "avatar_profiles",
        "research_configurations",
        "research_jobs",
    ]

    all_tables_found = True
    for table in required_tables:
        if f"CREATE TABLE IF NOT EXISTS {table}" in content:
            print(f"✅ TABLE: {table}")
        else:
            print(f"❌ MISSING TABLE: {table}")
            all_tables_found = False

    return all_tables_found


def verify_configuration():
    """Verify production configuration template"""
    print("\n🔍 Verifying configuration...")

    config_file = "config/production.env.template"
    if not check_file_exists(config_file):
        print(f"❌ MISSING: {config_file}")
        return False

    with open(config_file, "r") as f:
        content = f.read()

    # Check for key configuration sections
    required_sections = [
        "SUPABASE_URL",
        "OPENAI_API_KEY",
        "HEYGEN_API_KEY",
        "AYRSHARE_API_KEY",
        "JWT_SECRET",
        "CORS_ORIGINS",
    ]

    all_configs_found = True
    for config in required_sections:
        if config in content:
            print(f"✅ CONFIG: {config}")
        else:
            print(f"❌ MISSING CONFIG: {config}")
            all_configs_found = False

    return all_configs_found


def main():
    """Run all verification checks"""
    print("🧹 Social Media Module Cleanup Verification")
    print("=" * 50)

    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    checks = [
        ("Deprecated Code Removal", verify_deprecated_removal),
        ("Core Files", verify_core_files),
        ("Import System", verify_imports),
        ("Database Schema", verify_database_schema),
        ("Configuration", verify_configuration),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ ERROR in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 ALL CHECKS PASSED! Cleanup successful!")
        print("✅ Social media module is clean and production-ready")
        return 0
    else:
        print(f"\n⚠️  {total - passed} checks failed. Review issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
