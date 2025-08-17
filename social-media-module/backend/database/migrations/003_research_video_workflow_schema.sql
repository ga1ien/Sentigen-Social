-- Research-to-Video Workflow Schema Migration
-- Adds tables for the complete research-to-video workflow

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Workflow approvals table (for manual approval step)
CREATE TABLE IF NOT EXISTS workflow_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT NOT NULL UNIQUE,
    script TEXT NOT NULL,
    video_result JSONB NOT NULL,
    config JSONB NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow results table (final results storage)
CREATE TABLE IF NOT EXISTS workflow_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    generated_script TEXT,
    video_url TEXT,
    video_metadata JSONB DEFAULT '{}',
    approval_status TEXT,
    published_post_ids JSONB DEFAULT '[]',
    error_message TEXT,
    execution_time FLOAT,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video generation tasks table (for tracking HeyGen jobs)
CREATE TABLE IF NOT EXISTS video_generation_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT NOT NULL,
    heygen_task_id TEXT,
    script TEXT NOT NULL,
    avatar_id TEXT,
    voice_id TEXT,
    video_style TEXT DEFAULT 'professional',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    video_url TEXT,
    thumbnail_url TEXT,
    duration FLOAT,
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Research sessions table (for tracking research phases)
CREATE TABLE IF NOT EXISTS research_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT NOT NULL,
    topics JSONB NOT NULL,
    platforms JSONB NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    insights_count INTEGER DEFAULT 0,
    top_insights JSONB DEFAULT '[]',
    trending_topics JSONB DEFAULT '[]',
    sentiment_analysis JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Script generation history table
CREATE TABLE IF NOT EXISTS script_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT NOT NULL,
    research_session_id UUID REFERENCES research_sessions(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    generated_script TEXT,
    target_audience TEXT,
    video_style TEXT,
    duration_target INTEGER,
    model_used TEXT,
    generation_time FLOAT,
    quality_score FLOAT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- TikTok posts table (specific tracking for TikTok publications)
CREATE TABLE IF NOT EXISTS tiktok_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT NOT NULL,
    post_id TEXT NOT NULL,
    video_url TEXT NOT NULL,
    caption TEXT,
    hashtags JSONB DEFAULT '[]',
    status TEXT DEFAULT 'published' CHECK (status IN ('published', 'failed', 'removed')),
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    published_at TIMESTAMP WITH TIME ZONE,
    last_analytics_update TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow analytics table (performance tracking)
CREATE TABLE IF NOT EXISTS workflow_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT NOT NULL,
    research_duration FLOAT,
    script_generation_duration FLOAT,
    video_generation_duration FLOAT,
    total_execution_time FLOAT,
    insights_extracted INTEGER DEFAULT 0,
    trending_topics_found INTEGER DEFAULT 0,
    video_quality_score FLOAT,
    engagement_prediction FLOAT,
    actual_engagement FLOAT,
    success_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_workflow_approvals_workflow_id ON workflow_approvals(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_approvals_status ON workflow_approvals(status);
CREATE INDEX IF NOT EXISTS idx_workflow_results_workflow_id ON workflow_results(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_results_status ON workflow_results(status);
CREATE INDEX IF NOT EXISTS idx_video_tasks_workflow_id ON video_generation_tasks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_video_tasks_status ON video_generation_tasks(status);
CREATE INDEX IF NOT EXISTS idx_video_tasks_heygen_id ON video_generation_tasks(heygen_task_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_workflow_id ON research_sessions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_script_generations_workflow_id ON script_generations(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tiktok_posts_workflow_id ON tiktok_posts(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tiktok_posts_post_id ON tiktok_posts(post_id);
CREATE INDEX IF NOT EXISTS idx_workflow_analytics_workflow_id ON workflow_analytics(workflow_id);

-- Updated at triggers
CREATE TRIGGER update_workflow_approvals_updated_at 
    BEFORE UPDATE ON workflow_approvals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_video_tasks_updated_at 
    BEFORE UPDATE ON video_generation_tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tiktok_posts_updated_at 
    BEFORE UPDATE ON tiktok_posts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for easier querying
CREATE OR REPLACE VIEW workflow_overview AS
SELECT 
    we.id as workflow_id,
    we.workflow_name,
    we.status,
    we.progress,
    we.started_at,
    we.completed_at,
    we.user_id,
    we.workspace_id,
    rs.insights_count,
    rs.trending_topics,
    sg.generated_script IS NOT NULL as has_script,
    vgt.video_url IS NOT NULL as has_video,
    wa.status as approval_status,
    tp.post_id as tiktok_post_id,
    tp.engagement_rate
FROM workflow_executions we
LEFT JOIN research_sessions rs ON we.id = rs.workflow_id
LEFT JOIN script_generations sg ON we.id = sg.workflow_id
LEFT JOIN video_generation_tasks vgt ON we.id = vgt.workflow_id
LEFT JOIN workflow_approvals wa ON we.id = wa.workflow_id
LEFT JOIN tiktok_posts tp ON we.id = tp.workflow_id
WHERE we.workflow_name = 'research_to_video';

-- Function to get workflow progress percentage
CREATE OR REPLACE FUNCTION get_workflow_progress(workflow_id_param TEXT)
RETURNS FLOAT AS $$
DECLARE
    current_status TEXT;
    progress_value FLOAT;
BEGIN
    SELECT status INTO current_status 
    FROM workflow_executions 
    WHERE id = workflow_id_param;
    
    progress_value := CASE current_status
        WHEN 'pending' THEN 0
        WHEN 'researching' THEN 20
        WHEN 'analyzing' THEN 40
        WHEN 'script_generation' THEN 60
        WHEN 'video_generation' THEN 80
        WHEN 'awaiting_approval' THEN 90
        WHEN 'approved' THEN 95
        WHEN 'publishing' THEN 98
        WHEN 'completed' THEN 100
        WHEN 'failed' THEN 0
        WHEN 'cancelled' THEN 0
        ELSE 0
    END;
    
    RETURN progress_value;
END;
$$ LANGUAGE plpgsql;

-- Function to update TikTok analytics
CREATE OR REPLACE FUNCTION update_tiktok_analytics(
    post_id_param TEXT,
    views_param INTEGER DEFAULT NULL,
    likes_param INTEGER DEFAULT NULL,
    comments_param INTEGER DEFAULT NULL,
    shares_param INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE tiktok_posts SET
        views_count = COALESCE(views_param, views_count),
        likes_count = COALESCE(likes_param, likes_count),
        comments_count = COALESCE(comments_param, comments_count),
        shares_count = COALESCE(shares_param, shares_count),
        engagement_rate = CASE 
            WHEN COALESCE(views_param, views_count) > 0 THEN
                (COALESCE(likes_param, likes_count) + 
                 COALESCE(comments_param, comments_count) + 
                 COALESCE(shares_param, shares_count))::FLOAT / 
                COALESCE(views_param, views_count)::FLOAT * 100
            ELSE 0
        END,
        last_analytics_update = NOW(),
        updated_at = NOW()
    WHERE post_id = post_id_param;
END;
$$ LANGUAGE plpgsql;
