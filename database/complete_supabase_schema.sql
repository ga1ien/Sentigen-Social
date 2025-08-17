-- =====================================================
-- COMPLETE SUPABASE SCHEMA FOR SENTIGEN SOCIAL
-- Updated: December 19, 2024
-- Includes: Core platform + Avatar system + Research workflows
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- CORE PLATFORM TABLES
-- =====================================================

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'starter', 'creator', 'creator_pro', 'enterprise')),
    is_admin BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workspaces table
CREATE TABLE IF NOT EXISTS public.workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workspace members table
CREATE TABLE IF NOT EXISTS public.workspace_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'editor', 'member')),
    permissions JSONB DEFAULT '{}',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workspace_id, user_id)
);

-- =====================================================
-- SOCIAL MEDIA PLATFORM TABLES
-- =====================================================

-- Social media platforms
CREATE TABLE IF NOT EXISTS public.social_platforms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    icon_url TEXT,
    api_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User social media accounts
CREATE TABLE IF NOT EXISTS public.user_social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    platform_id UUID REFERENCES public.social_platforms(id) ON DELETE CASCADE,
    account_name TEXT NOT NULL,
    account_id TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    account_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, workspace_id, platform_id, account_id)
);

-- =====================================================
-- CONTENT MANAGEMENT TABLES
-- =====================================================

-- Content posts
CREATE TABLE IF NOT EXISTS public.content_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT,
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'text' CHECK (content_type IN ('text', 'image', 'video', 'carousel', 'story')),
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'archived')),
    scheduled_for TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content media attachments
CREATE TABLE IF NOT EXISTS public.content_media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES public.content_posts(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    alt_text TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Post publishing to platforms
CREATE TABLE IF NOT EXISTS public.post_publications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES public.content_posts(id) ON DELETE CASCADE,
    account_id UUID REFERENCES public.user_social_accounts(id) ON DELETE CASCADE,
    platform_post_id TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'failed', 'deleted')),
    published_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    platform_response JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- AVATAR SYSTEM TABLES (From TikClip Integration)
-- =====================================================

-- Avatar profiles for video generation
CREATE TABLE IF NOT EXISTS public.avatar_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    avatar_id VARCHAR(100) NOT NULL,
    voice_id VARCHAR(100) NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    description TEXT,
    preview_url TEXT,
    avatar_type VARCHAR(20) DEFAULT 'talking_photo' CHECK (avatar_type IN ('talking_photo', 'avatar', 'custom')),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI-generated scripts for videos
CREATE TABLE IF NOT EXISTS public.script_generations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    topic VARCHAR(120) NOT NULL,
    script TEXT NOT NULL,
    target_audience TEXT DEFAULT 'general audience',
    video_style TEXT DEFAULT 'professional',
    duration_target INTEGER DEFAULT 60,
    model_used TEXT,
    quality_score FLOAT DEFAULT 0.5 CHECK (quality_score >= 0 AND quality_score <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video generation tracking
CREATE TABLE IF NOT EXISTS public.video_generations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    script_id INTEGER REFERENCES public.script_generations(id) ON DELETE SET NULL,
    profile_id INTEGER REFERENCES public.avatar_profiles(id) ON DELETE SET NULL,
    heygen_video_id VARCHAR(100) NOT NULL UNIQUE,
    video_url TEXT,
    thumbnail_url TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    aspect_ratio VARCHAR(20) DEFAULT 'landscape' CHECK (aspect_ratio IN ('landscape', 'portrait', 'square')),
    duration FLOAT,
    avatar_id VARCHAR(100), -- For backward compatibility
    voice_id VARCHAR(100),  -- For backward compatibility
    is_public BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Video performance analytics
CREATE TABLE IF NOT EXISTS public.video_analytics (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES public.video_generations(id) ON DELETE CASCADE,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0 CHECK (engagement_rate >= 0 AND engagement_rate <= 1),
    watch_time_avg FLOAT,
    completion_rate FLOAT CHECK (completion_rate >= 0 AND completion_rate <= 1),
    platform_data JSONB DEFAULT '{}',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User video generation limits
CREATE TABLE IF NOT EXISTS public.user_video_limits (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE UNIQUE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'starter', 'creator', 'creator_pro', 'enterprise')),
    monthly_limit INTEGER DEFAULT 1,
    videos_this_month INTEGER DEFAULT 0,
    credits_reset_at TIMESTAMP WITH TIME ZONE,
    is_admin BOOLEAN DEFAULT FALSE,
    premium_until TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Avatar usage statistics
CREATE TABLE IF NOT EXISTS public.avatar_usage_stats (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES public.avatar_profiles(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    usage_count INTEGER DEFAULT 0,
    total_video_duration FLOAT DEFAULT 0,
    avg_quality_score FLOAT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- RESEARCH & WORKFLOW TABLES
-- =====================================================

-- Workflow executions (for research-to-video workflows)
CREATE TABLE IF NOT EXISTS public.workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_config JSONB NOT NULL,
    tasks TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress FLOAT DEFAULT 0.0 CHECK (progress >= 0 AND progress <= 1),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '{}',
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content insights from research
CREATE TABLE IF NOT EXISTS public.content_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workflow_id UUID REFERENCES public.workflow_executions(id) ON DELETE SET NULL,
    source_platform TEXT NOT NULL,
    source_url TEXT,
    title TEXT,
    content TEXT,
    author TEXT,
    engagement_score FLOAT DEFAULT 0,
    sentiment_score FLOAT,
    keywords TEXT[] DEFAULT '{}',
    topics TEXT[] DEFAULT '{}',
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content recommendations
CREATE TABLE IF NOT EXISTS public.content_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    content_type TEXT DEFAULT 'post' CHECK (content_type IN ('post', 'video', 'story', 'carousel')),
    recommended_platforms TEXT[] DEFAULT '{}',
    confidence_score FLOAT DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning TEXT,
    suggested_content TEXT,
    tags TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'implemented')),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- ANALYTICS & REPORTING TABLES
-- =====================================================

-- Platform analytics
CREATE TABLE IF NOT EXISTS public.platform_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES public.user_social_accounts(id) ON DELETE CASCADE,
    post_id UUID REFERENCES public.content_posts(id) ON DELETE SET NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_type TEXT DEFAULT 'count' CHECK (metric_type IN ('count', 'rate', 'duration', 'percentage')),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User activity logs
CREATE TABLE IF NOT EXISTS public.user_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Core platform indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON public.users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_workspaces_owner_id ON public.workspaces(owner_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace_id ON public.workspace_members(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_user_id ON public.workspace_members(user_id);

-- Social media indexes
CREATE INDEX IF NOT EXISTS idx_user_social_accounts_user_id ON public.user_social_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_social_accounts_workspace_id ON public.user_social_accounts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_user_social_accounts_platform_id ON public.user_social_accounts(platform_id);

-- Content indexes
CREATE INDEX IF NOT EXISTS idx_content_posts_workspace_id ON public.content_posts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_content_posts_user_id ON public.content_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_content_posts_status ON public.content_posts(status);
CREATE INDEX IF NOT EXISTS idx_content_posts_scheduled_for ON public.content_posts(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_content_posts_created_at ON public.content_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_media_post_id ON public.content_media(post_id);
CREATE INDEX IF NOT EXISTS idx_post_publications_post_id ON public.post_publications(post_id);
CREATE INDEX IF NOT EXISTS idx_post_publications_account_id ON public.post_publications(account_id);

-- Avatar system indexes
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_workspace_id ON public.avatar_profiles(workspace_id);
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_display_order ON public.avatar_profiles(display_order);
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_avatar_id ON public.avatar_profiles(avatar_id);
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_is_default ON public.avatar_profiles(is_default);
CREATE INDEX IF NOT EXISTS idx_script_generations_user_id ON public.script_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_script_generations_workspace_id ON public.script_generations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_script_generations_created_at ON public.script_generations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_generations_user_id ON public.video_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_video_generations_workspace_id ON public.video_generations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_video_generations_status ON public.video_generations(status);
CREATE INDEX IF NOT EXISTS idx_video_generations_heygen_id ON public.video_generations(heygen_video_id);
CREATE INDEX IF NOT EXISTS idx_video_analytics_video_id ON public.video_analytics(video_id);
CREATE INDEX IF NOT EXISTS idx_user_video_limits_user_id ON public.user_video_limits(user_id);

-- Research & workflow indexes
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workspace_id ON public.workflow_executions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_user_id ON public.workflow_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON public.workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_content_insights_workspace_id ON public.content_insights(workspace_id);
CREATE INDEX IF NOT EXISTS idx_content_insights_workflow_id ON public.content_insights(workflow_id);
CREATE INDEX IF NOT EXISTS idx_content_recommendations_workspace_id ON public.content_recommendations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_content_recommendations_status ON public.content_recommendations(status);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_platform_analytics_account_id ON public.platform_analytics(account_id);
CREATE INDEX IF NOT EXISTS idx_platform_analytics_post_id ON public.platform_analytics(post_id);
CREATE INDEX IF NOT EXISTS idx_platform_analytics_recorded_at ON public.platform_analytics(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON public.user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_workspace_id ON public.user_activity_logs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON public.user_activity_logs(created_at DESC);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT COLUMNS
-- =====================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
DO $$
BEGIN
    -- Users table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at') THEN
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON public.users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- Workspaces table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_workspaces_updated_at') THEN
        CREATE TRIGGER update_workspaces_updated_at
        BEFORE UPDATE ON public.workspaces
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- Content posts table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_content_posts_updated_at') THEN
        CREATE TRIGGER update_content_posts_updated_at
        BEFORE UPDATE ON public.content_posts
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- Avatar profiles table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_avatar_profiles_updated_at') THEN
        CREATE TRIGGER update_avatar_profiles_updated_at
        BEFORE UPDATE ON public.avatar_profiles
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- User video limits table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_user_video_limits_updated_at') THEN
        CREATE TRIGGER update_user_video_limits_updated_at
        BEFORE UPDATE ON public.user_video_limits
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- Avatar usage stats table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_avatar_usage_stats_updated_at') THEN
        CREATE TRIGGER update_avatar_usage_stats_updated_at
        BEFORE UPDATE ON public.avatar_usage_stats
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- Workflow executions table
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_workflow_executions_updated_at') THEN
        CREATE TRIGGER update_workflow_executions_updated_at
        BEFORE UPDATE ON public.workflow_executions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Function to reset monthly video credits
CREATE OR REPLACE FUNCTION reset_monthly_video_credits()
RETURNS void AS $$
DECLARE
    tier_limits JSONB := '{
        "free": 1,
        "starter": 3,
        "creator": 8,
        "creator_pro": 15,
        "enterprise": 50
    }';
BEGIN
    UPDATE public.user_video_limits 
    SET 
        videos_this_month = 0,
        monthly_limit = (tier_limits->>subscription_tier)::INTEGER,
        credits_reset_at = DATE_TRUNC('month', NOW()) + INTERVAL '1 month',
        updated_at = NOW()
    WHERE 
        credits_reset_at IS NULL 
        OR credits_reset_at <= NOW()
        OR DATE_TRUNC('month', credits_reset_at) < DATE_TRUNC('month', NOW());
END;
$$ LANGUAGE plpgsql;

-- Function to check video creation limits
CREATE OR REPLACE FUNCTION check_video_creation_limit(p_user_id UUID, p_workspace_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_limits RECORD;
    can_create BOOLEAN := FALSE;
BEGIN
    SELECT * INTO user_limits 
    FROM public.user_video_limits 
    WHERE user_id = p_user_id;
    
    IF NOT FOUND THEN
        INSERT INTO public.user_video_limits (user_id, workspace_id, subscription_tier, monthly_limit, videos_this_month, credits_reset_at)
        VALUES (p_user_id, p_workspace_id, 'free', 1, 0, DATE_TRUNC('month', NOW()) + INTERVAL '1 month')
        RETURNING * INTO user_limits;
    END IF;
    
    PERFORM reset_monthly_video_credits();
    
    SELECT * INTO user_limits 
    FROM public.user_video_limits 
    WHERE user_id = p_user_id;
    
    IF user_limits.is_admin THEN
        can_create := TRUE;
    ELSIF user_limits.videos_this_month < user_limits.monthly_limit THEN
        can_create := TRUE;
        UPDATE public.user_video_limits 
        SET videos_this_month = videos_this_month + 1,
            updated_at = NOW()
        WHERE user_id = p_user_id;
    END IF;
    
    RETURN can_create;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- INITIAL DATA SETUP
-- =====================================================

-- Insert default social platforms
INSERT INTO public.social_platforms (name, display_name, icon_url, is_active) VALUES
    ('linkedin', 'LinkedIn', '/icons/linkedin.svg', true),
    ('twitter', 'X (Twitter)', '/icons/twitter.svg', true),
    ('facebook', 'Facebook', '/icons/facebook.svg', true),
    ('instagram', 'Instagram', '/icons/instagram.svg', true),
    ('tiktok', 'TikTok', '/icons/tiktok.svg', true),
    ('youtube', 'YouTube', '/icons/youtube.svg', true),
    ('pinterest', 'Pinterest', '/icons/pinterest.svg', true)
ON CONFLICT (name) DO NOTHING;

-- Insert default avatar profiles (placeholder - replace with actual HeyGen IDs)
INSERT INTO public.avatar_profiles (name, avatar_id, voice_id, display_order, is_default, description, avatar_type) VALUES
    ('Professional Male', 'default_male_avatar', 'default_male_voice', 0, TRUE, 'Professional male avatar suitable for business content', 'avatar'),
    ('Professional Female', 'default_female_avatar', 'default_female_voice', 1, FALSE, 'Professional female avatar suitable for business content', 'avatar'),
    ('Casual Male', 'casual_male_avatar', 'casual_male_voice', 2, FALSE, 'Casual male avatar for informal content', 'talking_photo'),
    ('Casual Female', 'casual_female_avatar', 'casual_female_voice', 3, FALSE, 'Casual female avatar for informal content', 'talking_photo')
ON CONFLICT DO NOTHING;

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_social_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.content_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.content_media ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_publications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.avatar_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.script_generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.video_generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.video_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_video_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.avatar_usage_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.content_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.content_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.platform_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activity_logs ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (users can only access their own data)
CREATE POLICY "Users can view own profile" ON public.users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.users FOR UPDATE USING (auth.uid() = id);

-- Workspace-based policies (users can access data in workspaces they're members of)
CREATE POLICY "Users can view workspaces they're members of" ON public.workspaces FOR SELECT 
USING (
    id IN (
        SELECT workspace_id FROM public.workspace_members 
        WHERE user_id = auth.uid()
    )
);

-- Content policies
CREATE POLICY "Users can view content in their workspaces" ON public.content_posts FOR SELECT 
USING (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members 
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can create content in their workspaces" ON public.content_posts FOR INSERT 
WITH CHECK (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members 
        WHERE user_id = auth.uid()
    )
);

-- Avatar system policies
CREATE POLICY "Users can view avatar profiles in their workspaces" ON public.avatar_profiles FOR SELECT 
USING (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members 
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can view their own scripts" ON public.script_generations FOR SELECT 
USING (user_id = auth.uid());

CREATE POLICY "Users can create scripts" ON public.script_generations FOR INSERT 
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can view their own videos" ON public.video_generations FOR SELECT 
USING (user_id = auth.uid());

CREATE POLICY "Users can create videos" ON public.video_generations FOR INSERT 
WITH CHECK (user_id = auth.uid());

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE public.users IS 'Extended user profiles beyond Supabase auth.users';
COMMENT ON TABLE public.workspaces IS 'Team workspaces for organizing content and collaboration';
COMMENT ON TABLE public.workspace_members IS 'User membership and roles within workspaces';
COMMENT ON TABLE public.social_platforms IS 'Supported social media platforms';
COMMENT ON TABLE public.user_social_accounts IS 'Connected social media accounts per user/workspace';
COMMENT ON TABLE public.content_posts IS 'Content posts created by users';
COMMENT ON TABLE public.content_media IS 'Media attachments for content posts';
COMMENT ON TABLE public.post_publications IS 'Tracking of posts published to social platforms';
COMMENT ON TABLE public.avatar_profiles IS 'AI avatar configurations for video generation';
COMMENT ON TABLE public.script_generations IS 'AI-generated scripts for video content';
COMMENT ON TABLE public.video_generations IS 'Video generation requests and status tracking';
COMMENT ON TABLE public.video_analytics IS 'Performance analytics for generated videos';
COMMENT ON TABLE public.user_video_limits IS 'User subscription limits for video generation';
COMMENT ON TABLE public.avatar_usage_stats IS 'Usage statistics for avatar profiles';
COMMENT ON TABLE public.workflow_executions IS 'Automated workflow execution tracking';
COMMENT ON TABLE public.content_insights IS 'Research insights for content creation';
COMMENT ON TABLE public.content_recommendations IS 'AI-generated content recommendations';
COMMENT ON TABLE public.platform_analytics IS 'Social media platform performance metrics';
COMMENT ON TABLE public.user_activity_logs IS 'User activity audit trail';

-- =====================================================
-- SCHEMA COMPLETE
-- =====================================================

-- This schema includes:
-- ✅ Core platform (users, workspaces, teams)
-- ✅ Social media management (platforms, accounts, posts)
-- ✅ Content creation and publishing
-- ✅ Avatar system (profiles, scripts, videos)
-- ✅ Research workflows (insights, recommendations)
-- ✅ Analytics and reporting
-- ✅ User activity tracking
-- ✅ Row Level Security policies
-- ✅ Performance indexes
-- ✅ Utility functions
-- ✅ Initial data setup
