-- Enhanced Database Schema for GPT-5 Mini + Playwright + Supabase Architecture
-- Based on proven production system
-- Run this in your Supabase SQL Editor

-- Add columns for individual scraper insights
ALTER TABLE research_sessions
ADD COLUMN IF NOT EXISTS substack_insights JSONB;

ALTER TABLE research_sessions
ADD COLUMN IF NOT EXISTS linkedin_insights JSONB;

ALTER TABLE research_sessions
ADD COLUMN IF NOT EXISTS reddit_insights JSONB;

-- Add enhanced metadata columns
ALTER TABLE research_sessions
ADD COLUMN IF NOT EXISTS combined_analysis JSONB;

ALTER TABLE research_sessions
ADD COLUMN IF NOT EXISTS session_metadata JSONB;

-- Add performance tracking columns
ALTER TABLE research_sessions
ADD COLUMN IF NOT EXISTS extraction_stats JSONB;

ALTER TABLE research_sessions
ADD COLUMN IF NOT EXISTS quality_metrics JSONB;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_research_sessions_platforms ON research_sessions USING GIN (platforms);
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions (status);
CREATE INDEX IF NOT EXISTS idx_research_sessions_created_at ON research_sessions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_research_sessions_research_topic ON research_sessions (research_topic);

-- Create view for monitoring dashboard
CREATE OR REPLACE VIEW scraper_monitoring_view AS
SELECT
    id,
    research_topic,
    platforms,
    status,
    created_at,
    updated_at,
    CASE
        WHEN substack_insights IS NOT NULL THEN jsonb_array_length(substack_insights->'articles')
        ELSE 0
    END as substack_articles_count,
    CASE
        WHEN linkedin_insights IS NOT NULL THEN jsonb_array_length(linkedin_insights->'posts')
        ELSE 0
    END as linkedin_posts_count,
    CASE
        WHEN reddit_insights IS NOT NULL THEN jsonb_array_length(reddit_insights->'posts')
        ELSE 0
    END as reddit_posts_count,
    session_metadata->'duration' as session_duration,
    session_metadata->'scraper' as scraper_type,
    session_metadata->'intelligence' as ai_model
FROM research_sessions
ORDER BY created_at DESC;

-- Create function to get scraper statistics
CREATE OR REPLACE FUNCTION get_scraper_stats()
RETURNS TABLE (
    total_sessions bigint,
    completed_sessions bigint,
    running_sessions bigint,
    total_articles bigint,
    avg_session_duration numeric,
    top_platforms text[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_sessions,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_sessions,
        COUNT(*) FILTER (WHERE status = 'running') as running_sessions,
        (
            COALESCE(SUM(jsonb_array_length(substack_insights->'articles')), 0) +
            COALESCE(SUM(jsonb_array_length(linkedin_insights->'posts')), 0) +
            COALESCE(SUM(jsonb_array_length(reddit_insights->'posts')), 0)
        ) as total_articles,
        AVG((session_metadata->>'duration')::numeric) as avg_session_duration,
        ARRAY_AGG(DISTINCT platform) as top_platforms
    FROM research_sessions
    CROSS JOIN LATERAL unnest(platforms) as platform
    WHERE created_at > NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to research_sessions if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_research_sessions_updated_at'
    ) THEN
        CREATE TRIGGER update_research_sessions_updated_at
            BEFORE UPDATE ON research_sessions
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Verify all columns were added successfully
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'research_sessions'
AND column_name IN (
    'substack_insights',
    'linkedin_insights',
    'reddit_insights',
    'combined_analysis',
    'session_metadata',
    'extraction_stats',
    'quality_metrics'
)
ORDER BY column_name;

-- Show sample of the monitoring view
SELECT * FROM scraper_monitoring_view LIMIT 5;

-- Show current scraper statistics
SELECT * FROM get_scraper_stats();
