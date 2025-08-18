-- Content Intelligence Schema Migration (Chrome MCP references removed)

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Content insights table
CREATE TABLE IF NOT EXISTS content_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    engagement_score INTEGER DEFAULT 0,
    trending_topics JSONB DEFAULT '[]'::jsonb,
    sentiment TEXT DEFAULT 'neutral' CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    author TEXT,
    comments_summary TEXT,
    extracted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE
);

-- Content recommendations table
CREATE TABLE IF NOT EXISTS content_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    platforms JSONB DEFAULT '[]'::jsonb,
    estimated_engagement TEXT DEFAULT 'medium' CHECK (estimated_engagement IN ('high', 'medium', 'low')),
    content_type TEXT DEFAULT 'article',
    keywords JSONB DEFAULT '[]'::jsonb,
    target_audience TEXT,
    content_angle TEXT,
    best_posting_time TEXT,
    hashtags JSONB DEFAULT '[]'::jsonb,
    key_talking_points JSONB DEFAULT '[]'::jsonb,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE
);

-- Scan history table
CREATE TABLE IF NOT EXISTS scan_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id TEXT UNIQUE NOT NULL,
    platforms JSONB NOT NULL DEFAULT '[]'::jsonb,
    search_queries JSONB DEFAULT '[]'::jsonb,
    insights_count INTEGER DEFAULT 0,
    trending_topics JSONB DEFAULT '{}'::jsonb,
    engagement_analysis JSONB DEFAULT '{}'::jsonb,
    scan_duration_seconds NUMERIC DEFAULT 0,
    success_rate NUMERIC DEFAULT 0,
    scan_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE
);

-- Scheduled scans table
CREATE TABLE IF NOT EXISTS scheduled_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id TEXT UNIQUE NOT NULL,
    platforms JSONB NOT NULL DEFAULT '[]'::jsonb,
    search_queries JSONB DEFAULT '[]'::jsonb,
    interval_hours INTEGER NOT NULL DEFAULT 6,
    max_posts_per_platform INTEGER DEFAULT 20,
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'running', 'paused', 'error', 'cancelled')),
    next_run TIMESTAMP WITH TIME ZONE NOT NULL,
    last_run TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    error_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE
);

-- Removed Chrome MCP sessions table

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_content_insights_platform ON content_insights(platform);
CREATE INDEX IF NOT EXISTS idx_content_insights_extracted_at ON content_insights(extracted_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_insights_engagement ON content_insights(engagement_score DESC);
CREATE INDEX IF NOT EXISTS idx_content_insights_workspace ON content_insights(workspace_id);
CREATE INDEX IF NOT EXISTS idx_content_insights_trending_topics ON content_insights USING GIN(trending_topics);

CREATE INDEX IF NOT EXISTS idx_content_recommendations_generated_at ON content_recommendations(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_recommendations_workspace ON content_recommendations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_content_recommendations_engagement ON content_recommendations(estimated_engagement);

CREATE INDEX IF NOT EXISTS idx_scan_history_scan_timestamp ON scan_history(scan_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scan_history_workspace ON scan_history(workspace_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_scan_id ON scan_history(scan_id);

CREATE INDEX IF NOT EXISTS idx_scheduled_scans_next_run ON scheduled_scans(next_run);
CREATE INDEX IF NOT EXISTS idx_scheduled_scans_status ON scheduled_scans(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_scans_workspace ON scheduled_scans(workspace_id);

-- Removed Chrome MCP session indexes

-- Full-text search indexes for content
CREATE INDEX IF NOT EXISTS idx_content_insights_title_fts ON content_insights USING GIN(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_content_insights_content_fts ON content_insights USING GIN(to_tsvector('english', content));

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_content_insights_updated_at
    BEFORE UPDATE ON content_insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scheduled_scans_updated_at
    BEFORE UPDATE ON scheduled_scans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE content_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_scans ENABLE ROW LEVEL SECURITY;
-- Removed RLS for chrome MCP sessions

-- Policies for content_insights
CREATE POLICY "Users can view their workspace insights" ON content_insights
    FOR SELECT USING (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert insights to their workspace" ON content_insights
    FOR INSERT WITH CHECK (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can update their workspace insights" ON content_insights
    FOR UPDATE USING (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can delete their workspace insights" ON content_insights
    FOR DELETE USING (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

-- Policies for content_recommendations
CREATE POLICY "Users can view their workspace recommendations" ON content_recommendations
    FOR SELECT USING (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert recommendations to their workspace" ON content_recommendations
    FOR INSERT WITH CHECK (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can update their workspace recommendations" ON content_recommendations
    FOR UPDATE USING (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can delete their workspace recommendations" ON content_recommendations
    FOR DELETE USING (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

-- Policies for scan_history
CREATE POLICY "Users can view their workspace scan history" ON scan_history
    FOR SELECT USING (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert scan history to their workspace" ON scan_history
    FOR INSERT WITH CHECK (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

-- Policies for scheduled_scans
CREATE POLICY "Users can manage their workspace scheduled scans" ON scheduled_scans
    FOR ALL USING (workspace_id IN (
        SELECT id FROM workspaces WHERE user_id = auth.uid()
    ));

-- Removed policies for chrome MCP sessions

-- Views for analytics
CREATE OR REPLACE VIEW content_insights_analytics AS
SELECT
    platform,
    DATE_TRUNC('day', extracted_at) as date,
    COUNT(*) as insights_count,
    AVG(engagement_score) as avg_engagement,
    MAX(engagement_score) as max_engagement,
    COUNT(DISTINCT author) as unique_authors,
    jsonb_array_elements_text(trending_topics) as topic
FROM content_insights
WHERE extracted_at >= NOW() - INTERVAL '30 days'
GROUP BY platform, DATE_TRUNC('day', extracted_at), jsonb_array_elements_text(trending_topics);

CREATE OR REPLACE VIEW trending_topics_summary AS
SELECT
    topic,
    COUNT(*) as frequency,
    AVG(engagement_score) as avg_engagement,
    ARRAY_AGG(DISTINCT platform) as platforms,
    MAX(extracted_at) as last_seen
FROM (
    SELECT
        jsonb_array_elements_text(trending_topics) as topic,
        platform,
        engagement_score,
        extracted_at
    FROM content_insights
    WHERE extracted_at >= NOW() - INTERVAL '7 days'
) t
GROUP BY topic
ORDER BY frequency DESC, avg_engagement DESC;

-- Function to clean old data
CREATE OR REPLACE FUNCTION cleanup_old_content_intelligence_data()
RETURNS void AS $$
BEGIN
    -- Delete insights older than 90 days
    DELETE FROM content_insights
    WHERE extracted_at < NOW() - INTERVAL '90 days';

    -- Delete scan history older than 180 days
    DELETE FROM scan_history
    WHERE scan_timestamp < NOW() - INTERVAL '180 days';

    -- Removed Chrome MCP session cleanup

    -- Log cleanup
    RAISE NOTICE 'Content intelligence data cleanup completed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-content-intelligence', '0 2 * * 0', 'SELECT cleanup_old_content_intelligence_data();');

COMMENT ON TABLE content_insights IS 'Stores content insights extracted from social media platforms';
COMMENT ON TABLE content_recommendations IS 'AI-generated content recommendations based on social media insights';
COMMENT ON TABLE scan_history IS 'History of platform scans and their results';
COMMENT ON TABLE scheduled_scans IS 'Configuration and status of scheduled recurring scans';
-- Removed comment for chrome MCP sessions

COMMENT ON COLUMN content_insights.trending_topics IS 'Array of trending topics/keywords extracted from content';
COMMENT ON COLUMN content_insights.metadata IS 'Additional metadata about the content extraction process';
COMMENT ON COLUMN content_recommendations.platforms IS 'Array of recommended platforms for the content';
COMMENT ON COLUMN content_recommendations.keywords IS 'Array of relevant keywords for the content';
COMMENT ON COLUMN scan_history.trending_topics IS 'Aggregated trending topics from the scan';
COMMENT ON COLUMN scan_history.engagement_analysis IS 'Analysis of engagement patterns from the scan';
