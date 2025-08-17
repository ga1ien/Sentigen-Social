#!/usr/bin/env python3
"""
Setup Reddit research schema in Supabase.
Adds all necessary tables for Reddit AI automation research.
"""

import asyncio
import os
import sys

import asyncpg
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()


async def setup_reddit_schema():
    """Set up Reddit research schema in Supabase."""
    print("🔧 Setting up Reddit Research Schema in Supabase")
    print("=" * 50)

    # Get Supabase connection details
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not service_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        print("Please set these in your .env file")
        return False

    # Extract database connection details from Supabase URL
    # Convert https://xxx.supabase.co to postgresql connection
    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
    db_url = f"postgresql://postgres:{service_key}@db.{project_id}.supabase.co:5432/postgres?sslmode=require"

    print(f"Connecting to Supabase project: {project_id}")

    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to Supabase PostgreSQL")

        # Read the Reddit schema SQL file
        schema_file = "REDDIT_SUPABASE_SCHEMA.sql"

        if not os.path.exists(schema_file):
            print(f"❌ Schema file not found: {schema_file}")
            return False

        with open(schema_file, "r") as f:
            schema_sql = f.read()

        print(f"📄 Read schema file: {schema_file}")

        # Execute the schema SQL
        print("🚀 Executing Reddit schema setup...")

        # Split SQL into individual statements and execute them
        statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]

        success_count = 0
        error_count = 0

        for i, statement in enumerate(statements, 1):
            try:
                if statement.strip():
                    await conn.execute(statement)
                    success_count += 1

                    # Show progress for major operations
                    if "CREATE TABLE" in statement:
                        table_name = statement.split("CREATE TABLE")[1].split("(")[0].strip()
                        print(f"   ✅ Created table: {table_name}")
                    elif "CREATE INDEX" in statement:
                        index_name = statement.split("CREATE INDEX")[1].split("ON")[0].strip()
                        print(f"   📊 Created index: {index_name}")
                    elif "INSERT INTO" in statement:
                        table_name = statement.split("INSERT INTO")[1].split("(")[0].strip()
                        print(f"   📝 Inserted data into: {table_name}")

            except Exception as e:
                error_msg = str(e)
                # Skip errors for things that already exist
                if "already exists" in error_msg or "duplicate key" in error_msg:
                    print(f"   ⚠️  Skipped (already exists): {error_msg.split(':')[0]}")
                else:
                    print(f"   ❌ Error in statement {i}: {error_msg}")
                    error_count += 1

        print(f"\n📊 Schema Setup Results:")
        print(f"   ✅ Successful statements: {success_count}")
        print(f"   ❌ Failed statements: {error_count}")

        # Verify tables were created
        print(f"\n🔍 Verifying Reddit tables...")

        reddit_tables = [
            "reddit_research_sessions",
            "reddit_posts",
            "reddit_comments",
            "ai_automation_tools",
            "tool_mentions",
            "reddit_research_insights",
        ]

        for table in reddit_tables:
            try:
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = $1", table
                )
                if result > 0:
                    print(f"   ✅ Table exists: {table}")
                else:
                    print(f"   ❌ Table missing: {table}")
            except Exception as e:
                print(f"   ❌ Error checking table {table}: {str(e)}")

        # Check if AI automation tools were inserted
        try:
            tools_count = await conn.fetchval("SELECT COUNT(*) FROM ai_automation_tools")
            print(f"   📊 AI automation tools in database: {tools_count}")
        except Exception as e:
            print(f"   ⚠️  Could not count AI tools: {str(e)}")

        await conn.close()
        print("\n🎉 Reddit schema setup completed!")
        return True

    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        print("2. Ensure your Supabase project is active")
        print("3. Verify network connectivity")
        return False


async def test_reddit_schema():
    """Test the Reddit schema by creating a sample session."""
    print("\n🧪 Testing Reddit Schema")
    print("=" * 30)

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not service_key:
        print("❌ Missing Supabase credentials")
        return False

    try:
        from database.supabase_client import SupabaseClient

        supabase = SupabaseClient()

        # Test creating a research session
        test_session_data = {
            "session_name": "Test Reddit AI Research",
            "search_query": "AI automation tools test",
            "search_parameters": {
                "subreddits": ["artificial"],
                "target_tools": ["cassidy", "clickup"],
                "time_filter": "week",
            },
            "status": "completed",
            "ai_analysis_prompt": "Test analysis prompt",
        }

        # Insert test session
        result = supabase.service_client.table("reddit_research_sessions").insert(test_session_data).execute()

        if result.data:
            session_id = result.data[0]["id"]
            print(f"   ✅ Test session created: {session_id}")

            # Clean up test data
            supabase.service_client.table("reddit_research_sessions").delete().eq("id", session_id).execute()
            print(f"   🧹 Test session cleaned up")

            return True
        else:
            print("   ❌ Failed to create test session")
            return False

    except Exception as e:
        print(f"   ❌ Schema test failed: {str(e)}")
        return False


async def main():
    """Main setup function."""
    print("Reddit Research Schema Setup for Supabase")
    print("This will add all necessary tables for Reddit AI automation research")

    # Check environment
    if not os.path.exists(".env"):
        print("\n⚠️  No .env file found. Please create one with your Supabase credentials:")
        print("   SUPABASE_URL=https://your-project.supabase.co")
        print("   SUPABASE_SERVICE_KEY=your-service-role-key")
        return 1

    # Setup schema
    success = await setup_reddit_schema()

    if success:
        # Test schema
        test_success = await test_reddit_schema()

        if test_success:
            print("\n🎉 Reddit schema setup and testing completed successfully!")
            print("\nYou can now use the Reddit AI Research Worker with full Supabase integration.")
            print("\nNext steps:")
            print("1. Run: python test_reddit_ai_research.py")
            print("2. Or use the worker in your application")
        else:
            print("\n⚠️  Schema created but testing failed. Check your configuration.")
            return 1
    else:
        print("\n❌ Schema setup failed. Please check the errors above.")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
