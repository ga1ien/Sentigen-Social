-- =====================================================
-- Supabase Database Schema for AI Social Media Platform v2
-- Updated to match existing codebase patterns
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =====================================================
-- 1. WORKSPACES TABLE (Updated to match existing model)
-- =====================================================
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}',
    brand_guidelines JSONB DEFAULT '{}', -- Added from existing model
    social_accounts JSONB DEFAULT '[]', -- Added from existing model
    is_active BOOLEAN DEFAULT true, -- Added from existing model
    metadata JSONB DEFAULT '{}', -- Added from existing model
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 2. WORKSPACE MEMBERS TABLE (Keep as is - good design)
-- =====================================================
CREATE TABLE workspace_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'editor', 'member')),
    permissions JSONB DEFAULT '{}',
    invited_by UUID REFERENCES auth.users(id),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workspace_id, user_id)
);

-- =====================================================
-- 3. SOCIAL MEDIA POSTS TABLE (Updated to match existing)
-- =====================================================
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Changed from created_by
    title VARCHAR(500), -- Optional title
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text' CHECK (content_type IN ('text', 'image', 'video', 'carousel', 'story')),
    platforms TEXT[] DEFAULT '{}', -- Use TEXT[] like existing code
    media_assets TEXT[] DEFAULT '{}', -- Use TEXT[] for asset IDs
    hashtags TEXT[] DEFAULT '{}', -- Use TEXT[] like existing
    mentions TEXT[] DEFAULT '{}', -- Use TEXT[] like existing
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'cancelled')),
    scheduled_for TIMESTAMP WITH TIME ZONE, -- Match existing naming
    published_at TIMESTAMP WITH TIME ZONE,
    ayrshare_post_id VARCHAR(255), -- Added from existing schema
    platform_results JSONB DEFAULT '[]', -- Match existing naming
    analytics JSONB DEFAULT '{}', -- Match existing naming
    metadata JSONB DEFAULT '{}', -- Match existing naming
    -- AI-related fields
    ai_generated BOOLEAN DEFAULT false,
    ai_provider VARCHAR(100),
    ai_model VARCHAR(100),
    ai_prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 4. WORKER TASKS TABLE (From existing codebase)
-- =====================================================
CREATE TABLE worker_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    worker_type VARCHAR(50) NOT NULL, -- text, image, video, research, avatar_video
    task_type VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 1,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 300,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 5. WORKER RESULTS TABLE (From existing codebase)
-- =====================================================
CREATE TABLE worker_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES worker_tasks(id) ON DELETE CASCADE,
    worker_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    result_data JSONB,
    error_message TEXT,
    execution_time FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 6. MEDIA ASSETS TABLE (Updated to match existing)
-- =====================================================
CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Match existing
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL, -- Match existing
    media_type VARCHAR(50) NOT NULL, -- Match existing naming
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL, -- Added from existing
    url TEXT NOT NULL, -- Match existing
    thumbnail_url TEXT,
    dimensions JSONB, -- Match existing (width/height as JSON)
    duration FLOAT, -- For videos
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}', -- Match existing
    is_public BOOLEAN DEFAULT false, -- Match existing
    -- AI generation fields
    ai_generated BOOLEAN DEFAULT false,
    ai_provider VARCHAR(100),
    ai_model VARCHAR(100),
    ai_prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 7. CAMPAIGNS TABLE (From existing codebase)
-- =====================================================
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    objectives TEXT[] DEFAULT '{}',
    target_audience JSONB DEFAULT '{}',
    budget DECIMAL(10,2),
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    posts TEXT[] DEFAULT '{}', -- Array of post IDs
    status VARCHAR(50) DEFAULT 'draft',
    analytics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 8. CONTENT TEMPLATES TABLE (Updated to match existing)
-- =====================================================
CREATE TABLE content_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Match existing
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL, -- Match existing
    template_content TEXT NOT NULL,
    variables TEXT[] DEFAULT '{}', -- Match existing (TEXT[] not JSONB)
    platforms TEXT[] DEFAULT '{}', -- Match existing
    tags TEXT[] DEFAULT '{}', -- Match existing
    usage_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 9. WORKFLOW EXECUTIONS TABLE (From existing codebase)
-- =====================================================
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_config JSONB NOT NULL,
    tasks TEXT[] DEFAULT '{}', -- Array of task IDs
    status VARCHAR(50) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '{}',
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 10. CONTENT INSIGHTS TABLE (Chrome MCP - Match existing)
-- =====================================================
CREATE TABLE content_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    platform VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    engagement_score INTEGER,
    trending_topics JSONB DEFAULT '[]',
    sentiment VARCHAR(50),
    author VARCHAR(255),
    comments_summary TEXT,
    extracted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 11. CONTENT RECOMMENDATIONS TABLE (Chrome MCP)
-- =====================================================
CREATE TABLE content_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    platforms JSONB DEFAULT '[]',
    estimated_engagement VARCHAR(100),
    content_type VARCHAR(100),
    keywords JSONB DEFAULT '[]',
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 12. SCAN HISTORY TABLE (Chrome MCP)
-- =====================================================
CREATE TABLE scan_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    platforms JSONB DEFAULT '[]',
    search_queries JSONB DEFAULT '[]',
    insights_count INTEGER DEFAULT 0,
    trending_topics JSONB DEFAULT '[]',
    engagement_analysis JSONB DEFAULT '{}',
    scan_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 13. POST ANALYTICS TABLE (Separate from posts for better performance)
-- =====================================================
CREATE TABLE post_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    platform_post_id VARCHAR(255),
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0,
    raw_data JSONB DEFAULT '{}',
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(post_id, platform)
);

-- =====================================================
-- 14. USER PREFERENCES TABLE
-- =====================================================
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    theme VARCHAR(20) DEFAULT 'light' CHECK (theme IN ('light', 'dark', 'auto')),
    timezone VARCHAR(100) DEFAULT 'UTC',
    notification_settings JSONB DEFAULT '{}',
    ai_preferences JSONB DEFAULT '{}',
    dashboard_layout JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE (Match existing patterns)
-- =====================================================

-- Workspaces
CREATE INDEX idx_workspaces_owner_id ON workspaces(owner_id);

-- Posts
CREATE INDEX idx_posts_workspace_id ON posts(workspace_id);
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_scheduled_for ON posts(scheduled_for);
CREATE INDEX idx_posts_created_at ON posts(created_at);

-- Worker tasks
CREATE INDEX idx_tasks_workspace_id ON worker_tasks(workspace_id);
CREATE INDEX idx_tasks_status ON worker_tasks(status);
CREATE INDEX idx_tasks_worker_type ON worker_tasks(worker_type);
CREATE INDEX idx_tasks_scheduled_for ON worker_tasks(scheduled_for);

-- Worker results
CREATE INDEX idx_results_task_id ON worker_results(task_id);

-- Media assets
CREATE INDEX idx_media_workspace_id ON media_assets(workspace_id);
CREATE INDEX idx_media_user_id ON media_assets(user_id);
CREATE INDEX idx_media_type ON media_assets(media_type);

-- Campaigns
CREATE INDEX idx_campaigns_workspace_id ON campaigns(workspace_id);

-- Templates
CREATE INDEX idx_templates_workspace_id ON content_templates(workspace_id);
CREATE INDEX idx_templates_category ON content_templates(category);

-- Workflows
CREATE INDEX idx_workflows_workspace_id ON workflow_executions(workspace_id);

-- Content insights
CREATE INDEX idx_insights_workspace_id ON content_insights(workspace_id);
CREATE INDEX idx_insights_platform ON content_insights(platform);
CREATE INDEX idx_insights_extracted_at ON content_insights(extracted_at);

-- Analytics
CREATE INDEX idx_analytics_post_id ON post_analytics(post_id);
CREATE INDEX idx_analytics_platform ON post_analytics(platform);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Workspace-based access policies
CREATE POLICY "workspace_access" ON workspaces
    FOR ALL USING (
        owner_id = auth.uid() OR 
        id IN (SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid())
    );

CREATE POLICY "workspace_posts_access" ON posts
    FOR ALL USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE owner_id = auth.uid()
            UNION
            SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
        )
    );

-- Apply similar policies to all workspace-related tables
CREATE POLICY "workspace_tasks_access" ON worker_tasks
    FOR ALL USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE owner_id = auth.uid()
            UNION
            SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "workspace_media_access" ON media_assets
    FOR ALL USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE owner_id = auth.uid()
            UNION
            SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
        )
    );

-- User preferences policy
CREATE POLICY "user_preferences_access" ON user_preferences
    FOR ALL USING (user_id = auth.uid());

-- =====================================================
-- FUNCTIONS AND TRIGGERS (Match existing)
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers (match existing pattern)
CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON worker_tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_media_updated_at BEFORE UPDATE ON media_assets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON content_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflow_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SEED DATA
-- =====================================================

-- Insert default content templates
INSERT INTO content_templates (id, workspace_id, user_id, name, description, category, template_content, variables, platforms, is_public) VALUES
(uuid_generate_v4(), NULL, NULL, 'Product Launch', 'Template for announcing new products', 'Product', 'Excited to announce our new {{product_name}}! 🚀\n\n{{product_description}}\n\n#{{product_category}} #launch #innovation', ARRAY['product_name', 'product_description', 'product_category'], ARRAY['twitter', 'linkedin', 'facebook'], true),
(uuid_generate_v4(), NULL, NULL, 'Behind the Scenes', 'Show your team and process', 'Company', 'Take a look behind the scenes at {{company_name}}! 👀\n\n{{behind_scenes_description}}\n\n#BehindTheScenes #Team #{{company_name}}', ARRAY['company_name', 'behind_scenes_description'], ARRAY['instagram', 'twitter', 'linkedin'], true),
(uuid_generate_v4(), NULL, NULL, 'Tips & Advice', 'Share valuable tips with your audience', 'Educational', '💡 Pro Tip: {{tip_content}}\n\n{{additional_context}}\n\nWhat''s your experience with this? Let us know! 👇\n\n#Tips #{{industry}} #Advice', ARRAY['tip_content', 'additional_context', 'industry'], ARRAY['twitter', 'linkedin'], true);

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================
-- Schema v2 creation complete! 
-- Updated to match existing codebase patterns:
-- - TEXT[] arrays instead of JSONB for simple lists
-- - Consistent naming (user_id, scheduled_for, etc.)
-- - Added worker system tables
-- - Added campaigns and workflows
-- - Maintained Chrome MCP intelligence features
-- - Proper RLS and indexing
