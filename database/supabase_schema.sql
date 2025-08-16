-- =====================================================
-- Supabase Database Schema for AI Social Media Platform
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =====================================================
-- 1. WORKSPACES TABLE
-- =====================================================
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 2. WORKSPACE MEMBERS TABLE
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
-- 3. SOCIAL MEDIA ACCOUNTS TABLE
-- =====================================================
CREATE TABLE social_media_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('twitter', 'linkedin', 'facebook', 'instagram', 'tiktok', 'youtube')),
    account_name VARCHAR(255) NOT NULL,
    account_handle VARCHAR(255),
    account_id VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    account_data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    connected_by UUID REFERENCES auth.users(id),
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workspace_id, platform, account_id)
);

-- =====================================================
-- 4. CONTENT POSTS TABLE
-- =====================================================
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    title VARCHAR(500),
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text' CHECK (content_type IN ('text', 'image', 'video', 'carousel', 'story')),
    platforms JSONB NOT NULL DEFAULT '[]', -- Array of platforms
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'cancelled')),
    scheduled_for TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    tags JSONB DEFAULT '[]',
    hashtags JSONB DEFAULT '[]',
    mentions JSONB DEFAULT '[]',
    media_assets JSONB DEFAULT '[]', -- Array of media asset IDs
    ai_generated BOOLEAN DEFAULT false,
    ai_provider VARCHAR(100),
    ai_model VARCHAR(100),
    ai_prompt TEXT,
    performance_data JSONB DEFAULT '{}',
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 5. MEDIA ASSETS TABLE
-- =====================================================
CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    file_type VARCHAR(100) NOT NULL,
    file_size BIGINT,
    width INTEGER,
    height INTEGER,
    duration FLOAT, -- For videos
    storage_path TEXT NOT NULL,
    public_url TEXT,
    thumbnail_url TEXT,
    alt_text TEXT,
    metadata JSONB DEFAULT '{}',
    ai_generated BOOLEAN DEFAULT false,
    ai_provider VARCHAR(100),
    ai_model VARCHAR(100),
    ai_prompt TEXT,
    uploaded_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 6. POST ANALYTICS TABLE
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
-- 7. CONTENT TEMPLATES TABLE
-- =====================================================
CREATE TABLE content_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_content TEXT NOT NULL,
    category VARCHAR(100),
    platforms JSONB DEFAULT '[]',
    variables JSONB DEFAULT '[]', -- Template variables
    is_public BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 8. AI CONTENT GENERATIONS TABLE
-- =====================================================
CREATE TABLE ai_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('text', 'image', 'video', 'hashtags', 'caption')),
    prompt TEXT NOT NULL,
    generated_content TEXT,
    ai_provider VARCHAR(100) NOT NULL,
    ai_model VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{}',
    tokens_used INTEGER,
    cost_estimate DECIMAL(10,4),
    quality_score FLOAT,
    used_in_post UUID REFERENCES posts(id),
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 9. CONTENT CALENDAR TABLE
-- =====================================================
CREATE TABLE content_calendar (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    timezone VARCHAR(100) DEFAULT 'UTC',
    recurring_pattern VARCHAR(100), -- 'daily', 'weekly', 'monthly', etc.
    recurring_until DATE,
    notes TEXT,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 10. CONTENT INSIGHTS TABLE (Chrome MCP)
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
-- 13. USER PREFERENCES TABLE
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
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Workspaces indexes
CREATE INDEX idx_workspaces_owner ON workspaces(owner_id);

-- Workspace members indexes
CREATE INDEX idx_workspace_members_workspace ON workspace_members(workspace_id);
CREATE INDEX idx_workspace_members_user ON workspace_members(user_id);

-- Social media accounts indexes
CREATE INDEX idx_social_accounts_workspace ON social_media_accounts(workspace_id);
CREATE INDEX idx_social_accounts_platform ON social_media_accounts(platform);

-- Posts indexes
CREATE INDEX idx_posts_workspace ON posts(workspace_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_scheduled ON posts(scheduled_for);
CREATE INDEX idx_posts_created_by ON posts(created_by);
CREATE INDEX idx_posts_created_at ON posts(created_at);

-- Media assets indexes
CREATE INDEX idx_media_workspace ON media_assets(workspace_id);
CREATE INDEX idx_media_type ON media_assets(file_type);
CREATE INDEX idx_media_uploaded_by ON media_assets(uploaded_by);

-- Analytics indexes
CREATE INDEX idx_analytics_post ON post_analytics(post_id);
CREATE INDEX idx_analytics_platform ON post_analytics(platform);
CREATE INDEX idx_analytics_collected_at ON post_analytics(collected_at);

-- Content insights indexes
CREATE INDEX idx_insights_workspace ON content_insights(workspace_id);
CREATE INDEX idx_insights_platform ON content_insights(platform);
CREATE INDEX idx_insights_extracted_at ON content_insights(extracted_at);
CREATE INDEX idx_insights_engagement ON content_insights(engagement_score DESC);

-- AI generations indexes
CREATE INDEX idx_ai_generations_workspace ON ai_generations(workspace_id);
CREATE INDEX idx_ai_generations_type ON ai_generations(type);
CREATE INDEX idx_ai_generations_created_by ON ai_generations(created_by);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_media_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_calendar ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Workspaces policies
CREATE POLICY "Users can view workspaces they own or are members of" ON workspaces
    FOR SELECT USING (
        owner_id = auth.uid() OR 
        id IN (SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can create workspaces" ON workspaces
    FOR INSERT WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Workspace owners can update their workspaces" ON workspaces
    FOR UPDATE USING (owner_id = auth.uid());

CREATE POLICY "Workspace owners can delete their workspaces" ON workspaces
    FOR DELETE USING (owner_id = auth.uid());

-- Workspace members policies
CREATE POLICY "Users can view workspace members for their workspaces" ON workspace_members
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE owner_id = auth.uid()
            UNION
            SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
        )
    );

-- Posts policies
CREATE POLICY "Users can view posts in their workspaces" ON posts
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE owner_id = auth.uid()
            UNION
            SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create posts in their workspaces" ON posts
    FOR INSERT WITH CHECK (
        workspace_id IN (
            SELECT id FROM workspaces WHERE owner_id = auth.uid()
            UNION
            SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
        )
    );

-- Media assets policies
CREATE POLICY "Users can view media in their workspaces" ON media_assets
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE owner_id = auth.uid()
            UNION
            SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
        )
    );

-- User preferences policies
CREATE POLICY "Users can manage their own preferences" ON user_preferences
    FOR ALL USING (user_id = auth.uid());

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_social_accounts_updated_at BEFORE UPDATE ON social_media_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON content_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calendar_updated_at BEFORE UPDATE ON content_calendar
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INITIAL DATA / SEED DATA
-- =====================================================

-- Insert default content templates
INSERT INTO content_templates (id, workspace_id, name, description, template_content, category, platforms, variables, is_public, created_by) VALUES
(uuid_generate_v4(), NULL, 'Product Launch', 'Template for announcing new products', 'Excited to announce our new {{product_name}}! 🚀\n\n{{product_description}}\n\n#{{product_category}} #launch #innovation', 'Product', '["twitter", "linkedin", "facebook"]', '["product_name", "product_description", "product_category"]', true, NULL),
(uuid_generate_v4(), NULL, 'Behind the Scenes', 'Show your team and process', 'Take a look behind the scenes at {{company_name}}! 👀\n\n{{behind_scenes_description}}\n\n#BehindTheScenes #Team #{{company_name}}', 'Company', '["instagram", "twitter", "linkedin"]', '["company_name", "behind_scenes_description"]', true, NULL),
(uuid_generate_v4(), NULL, 'Tips & Advice', 'Share valuable tips with your audience', '💡 Pro Tip: {{tip_content}}\n\n{{additional_context}}\n\nWhat''s your experience with this? Let us know! 👇\n\n#Tips #{{industry}} #Advice', 'Educational', '["twitter", "linkedin"]', '["tip_content", "additional_context", "industry"]', true, NULL);

-- =====================================================
-- STORAGE BUCKETS (Run these in Supabase Dashboard)
-- =====================================================

-- Create storage bucket for media assets
-- INSERT INTO storage.buckets (id, name, public) VALUES ('media-assets', 'media-assets', true);

-- Storage policies for media assets
-- CREATE POLICY "Users can upload media to their workspace" ON storage.objects
--     FOR INSERT WITH CHECK (bucket_id = 'media-assets' AND auth.uid()::text = (storage.foldername(name))[1]);

-- CREATE POLICY "Users can view media from their workspace" ON storage.objects
--     FOR SELECT USING (bucket_id = 'media-assets' AND auth.uid()::text = (storage.foldername(name))[1]);

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================
-- Schema creation complete! 
-- Total tables: 13
-- Total indexes: 20+
-- RLS policies: Enabled with workspace-based access control
-- Triggers: Auto-update timestamps
-- Extensions: UUID, Crypto, Vector (for future AI features)
