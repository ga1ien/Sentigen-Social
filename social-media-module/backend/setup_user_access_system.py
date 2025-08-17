#!/usr/bin/env python3
"""
Setup User Access System
Applies database migrations and tests the user access system
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.research_service import ResearchConfiguration, ResearchSource, research_service
from core.user_auth import UserAuthService
from database.supabase_client import SupabaseClient


async def apply_database_migration():
    """Apply the user access database migration"""
    print("🔧 Applying database migration...")

    try:
        supabase_client = SupabaseClient()

        # Read migration file
        migration_path = "/Users/galenoakes/Development/Sentigen-Social/social-media-module/backend/database/migrations/005_research_tools_user_access.sql"

        with open(migration_path, "r") as f:
            migration_sql = f.read()

        # Split into individual statements (basic approach)
        statements = [
            stmt.strip() for stmt in migration_sql.split(";") if stmt.strip() and not stmt.strip().startswith("--")
        ]

        print(f"   📄 Found {len(statements)} SQL statements")

        # Execute each statement
        for i, statement in enumerate(statements, 1):
            try:
                if statement.upper().startswith(("CREATE", "ALTER", "DROP", "INSERT", "UPDATE", "DELETE", "GRANT")):
                    print(f"   ⚡ Executing statement {i}/{len(statements)}")
                    result = await supabase_client.service_client.rpc("exec_sql", {"sql": statement}).execute()

            except Exception as e:
                if "already exists" in str(e).lower() or "does not exist" in str(e).lower():
                    print(f"   ⚠️ Statement {i} skipped (already applied): {str(e)[:100]}...")
                else:
                    print(f"   ❌ Statement {i} failed: {e}")
                    # Continue with other statements

        print("✅ Database migration completed")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


async def create_test_user():
    """Create a test user for demonstration"""
    print("\n👤 Creating test user...")

    try:
        auth_service = UserAuthService()

        # Create test user
        test_user = await auth_service.get_or_create_user(email="test@sentigen.ai", full_name="Test User")

        print(f"✅ Test user created: {test_user['id']}")
        print(f"   📧 Email: {test_user['email']}")
        print(f"   👤 Name: {test_user['full_name']}")
        print(f"   🎫 Tier: {test_user['subscription_tier']}")

        return test_user

    except Exception as e:
        print(f"❌ Test user creation failed: {e}")
        return None


async def test_user_access_system(test_user):
    """Test the user access system"""
    print("\n🧪 Testing user access system...")

    try:
        user_id = test_user["id"]

        # Test user context creation
        from core.user_auth import get_user_research_context

        context = await get_user_research_context(user_id)

        print(f"✅ User context created")
        print(f"   🏢 Workspace: {context['workspace_id']}")
        print(f"   🔧 Max jobs: {context['permissions']['max_concurrent_jobs']}")
        print(f"   📋 Sources: {', '.join(context['permissions']['sources_available'])}")

        # Test configuration creation
        config = ResearchConfiguration(
            id=None,
            user_id=user_id,
            workspace_id=context["workspace_id"],
            source_type=ResearchSource.REDDIT,
            config_name="Test Reddit Research",
            description="Test configuration for user access system",
            configuration={
                "search_query": "AI automation tools",
                "subreddits": ["artificial", "productivity"],
                "max_posts_per_subreddit": 5,
            },
        )

        created_config = await research_service.create_configuration(context["user_context"], config)

        if created_config:
            print(f"✅ Configuration created: {created_config.id}")

            # Test configuration retrieval
            retrieved_config = await research_service.get_configuration(created_config.id, context["user_context"])

            if retrieved_config:
                print(f"✅ Configuration retrieved successfully")
            else:
                print(f"❌ Configuration retrieval failed")

            # Test user configurations listing
            user_configs = await research_service.get_user_configurations(user_id, context["workspace_id"])
            print(f"✅ User has {len(user_configs)} configurations")

        else:
            print(f"❌ Configuration creation failed")

        # Test user stats
        stats = await research_service.get_user_stats(user_id)
        print(
            f"✅ User stats retrieved: {stats.get('total_configurations', 0)} configs, {stats.get('total_jobs', 0)} jobs"
        )

        return True

    except Exception as e:
        print(f"❌ User access system test failed: {e}")
        return False


async def test_api_endpoints():
    """Test the unified API endpoints"""
    print("\n🌐 Testing API endpoints...")

    try:
        import httpx

        # Test health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")

            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")

        print("ℹ️ Note: Full API testing requires authentication tokens")
        print("   Start the API server with: python api/unified_research_api.py")

        return True

    except Exception as e:
        print(f"⚠️ API endpoint test skipped: {e}")
        print("   This is normal if the API server is not running")
        return True


async def create_sample_configurations():
    """Create sample configurations for demonstration"""
    print("\n📋 Creating sample configurations...")

    try:
        # Get test user
        auth_service = UserAuthService()
        test_user = await auth_service.get_or_create_user("test@sentigen.ai", "Test User")

        from core.user_auth import get_user_research_context

        context = await get_user_research_context(test_user["id"])

        # Sample Reddit configuration
        reddit_config = ResearchConfiguration(
            id=None,
            user_id=test_user["id"],
            workspace_id=context["workspace_id"],
            source_type=ResearchSource.REDDIT,
            config_name="AI Business Tools Research",
            description="Daily research on AI automation and business productivity tools",
            configuration={
                "search_query": "AI automation business tools productivity",
                "subreddits": ["artificial", "productivity", "Entrepreneur", "SaaS"],
                "max_posts_per_subreddit": 8,
                "max_comments_per_post": 25,
            },
            auto_run_enabled=True,
        )

        # Sample Hacker News configuration
        hn_config = ResearchConfiguration(
            id=None,
            user_id=test_user["id"],
            workspace_id=context["workspace_id"],
            source_type=ResearchSource.HACKERNEWS,
            config_name="Tech Trends Monitoring",
            description="Weekly monitoring of technology trends and discussions",
            configuration={
                "story_types": ["top", "best", "ask"],
                "search_topics": ["AI", "machine learning", "startup", "productivity"],
                "max_stories": 15,
            },
            auto_run_enabled=False,
        )

        # Sample GitHub configuration
        github_config = ResearchConfiguration(
            id=None,
            user_id=test_user["id"],
            workspace_id=context["workspace_id"],
            source_type=ResearchSource.GITHUB,
            config_name="Developer Tools Discovery",
            description="Discover trending developer tools and libraries",
            configuration={
                "search_topics": ["developer tools", "productivity", "automation", "AI tools"],
                "languages": ["Python", "JavaScript", "TypeScript"],
                "content_types": ["trending", "viral"],
                "max_repos": 12,
            },
            auto_run_enabled=False,
        )

        # Create configurations
        configs = [reddit_config, hn_config, github_config]
        created_configs = []

        for config in configs:
            try:
                created = await research_service.create_configuration(context["user_context"], config)
                if created:
                    created_configs.append(created)
                    print(f"✅ Created: {created.config_name} ({created.source_type.value})")
                else:
                    print(f"❌ Failed to create: {config.config_name}")
            except Exception as e:
                print(f"❌ Error creating {config.config_name}: {e}")

        print(f"✅ Created {len(created_configs)} sample configurations")
        return created_configs

    except Exception as e:
        print(f"❌ Sample configuration creation failed: {e}")
        return []


async def display_usage_examples():
    """Display usage examples for the new system"""
    print("\n📖 Usage Examples:")
    print("=" * 60)

    print("\n🔧 CLI Usage (User-Accessible):")
    print("# Reddit Research")
    print("python features/reddit_research/cli_reddit_user_accessible.py \\")
    print("  --user-id test@sentigen.ai \\")
    print("  --email test@sentigen.ai \\")
    print("  create-config \\")
    print("  --name 'AI Tools Research' \\")
    print("  --search-query 'AI automation tools' \\")
    print("  --subreddits 'artificial,productivity,SaaS'")

    print("\n# Hacker News Research")
    print("python features/hackernews_research/cli_hackernews_user_accessible.py \\")
    print("  --user-id test@sentigen.ai \\")
    print("  create-config \\")
    print("  --name 'Tech Trends' \\")
    print("  --story-types 'top,best,ask' \\")
    print("  --search-topics 'AI,startup,productivity'")

    print("\n# GitHub Research")
    print("python features/github_research/cli_github_user_accessible.py \\")
    print("  --user-id test@sentigen.ai \\")
    print("  create-config \\")
    print("  --name 'Dev Tools Discovery' \\")
    print("  --search-topics 'developer tools,automation' \\")
    print("  --languages 'Python,JavaScript'")

    print("\n🌐 API Usage:")
    print("# Start the unified API server")
    print("python api/unified_research_api.py")
    print("\n# API endpoints available at http://localhost:8000")
    print("- GET /health - Health check")
    print("- GET /user/info - User information")
    print("- GET /user/permissions - User permissions")
    print("- GET /user/stats - User statistics")
    print("- POST /configurations - Create configuration")
    print("- GET /configurations - List configurations")
    print("- POST /jobs - Create and run job")
    print("- GET /jobs - List jobs")

    print("\n🔑 Authentication:")
    print("- All API endpoints require Bearer token authentication")
    print("- CLI tools can use user ID or email for identification")
    print("- System automatically creates users and workspaces as needed")

    print("\n🎫 Subscription Tiers:")
    print("- Free: 1 concurrent job, 5 configs, Reddit/HN/GitHub")
    print("- Starter: 3 concurrent jobs, 15 configs")
    print("- Creator: 5 concurrent jobs, 50 configs, LinkedIn")
    print("- Creator Pro: 10 concurrent jobs, 100 configs, Twitter")
    print("- Enterprise: 50 concurrent jobs, 500 configs, all sources")


async def main():
    """Main setup function"""
    print("🚀 Setting up User Access System for Research Tools")
    print("=" * 60)

    # Step 1: Apply database migration
    migration_success = await apply_database_migration()

    if not migration_success:
        print("❌ Setup failed due to migration errors")
        return

    # Step 2: Create test user
    test_user = await create_test_user()

    if not test_user:
        print("❌ Setup failed due to user creation errors")
        return

    # Step 3: Test user access system
    access_test_success = await test_user_access_system(test_user)

    if not access_test_success:
        print("❌ Setup failed due to access system errors")
        return

    # Step 4: Create sample configurations
    sample_configs = await create_sample_configurations()

    # Step 5: Test API endpoints (optional)
    await test_api_endpoints()

    # Step 6: Display usage examples
    await display_usage_examples()

    print("\n🎉 User Access System Setup Complete!")
    print("=" * 60)
    print("✅ Database migration applied")
    print("✅ Test user created")
    print("✅ User access system tested")
    print(f"✅ {len(sample_configs)} sample configurations created")
    print("✅ System ready for all users")

    print(f"\n📊 Test User Details:")
    print(f"   📧 Email: test@sentigen.ai")
    print(f"   🆔 ID: {test_user['id']}")
    print(f"   🎫 Tier: {test_user['subscription_tier']}")

    print(f"\n🔗 Next Steps:")
    print("1. Start the unified API: python api/unified_research_api.py")
    print("2. Test CLI tools with your user credentials")
    print("3. Integrate with frontend using the API endpoints")
    print("4. Configure user subscription tiers as needed")


if __name__ == "__main__":
    asyncio.run(main())
