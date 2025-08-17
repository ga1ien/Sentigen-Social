-- =====================================================
-- INCREMENTAL SUPABASE SCHEMA FOR SENTIGEN SOCIAL
-- Safe to run multiple times - merges with existing data
-- Creates new tables if missing, adds columns if missing
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- UTILITY FUNCTIONS FOR SAFE SCHEMA UPDATES
-- =====================================================

-- Function to safely add columns
CREATE OR REPLACE FUNCTION add_column_if_not_exists(
    p_table_name TEXT,
    p_column_name TEXT,
    p_column_definition TEXT
) RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = p_table_name 
        AND column_name = p_column_name
    ) THEN
        EXECUTE format('ALTER TABLE public.%I ADD COLUMN %I %s', p_table_name, p_column_name, p_column_definition);
        RAISE NOTICE 'Added column %.% with definition: %', p_table_name, p_column_name, p_column_definition;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to safely create indexes
CREATE OR REPLACE FUNCTION create_index_if_not_exists(
    p_index_name TEXT,
    p_table_name TEXT,
    p_column_definition TEXT
) RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND indexname = p_index_name
    ) THEN
        EXECUTE format('CREATE INDEX %I ON public.%I %s', p_index_name, p_table_name, p_column_definition);
        RAISE NOTICE 'Created index: %', p_index_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

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

-- Add missing columns to users table if they don't exist
SELECT add_column_if_not_exists('users', 'subscription_tier', 'TEXT DEFAULT ''free'' CHECK (subscription_tier IN (''free'', ''starter'', ''creator'', ''creator_pro'', ''enterprise''))');
SELECT add_column_if_not_exists('users', 'is_admin', 'BOOLEAN DEFAULT FALSE');
SELECT add_column_if_not_exists('users', 'onboarding_completed', 'BOOLEAN DEFAULT FALSE');
SELECT add_column_if_not_exists('users', 'preferences', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('users', 'updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');

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

-- Add missing columns to workspaces table
SELECT add_column_if_not_exists('workspaces', 'description', 'TEXT');
SELECT add_column_if_not_exists('workspaces', 'settings', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('workspaces', 'updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');

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

-- Add missing columns to workspace_members table
SELECT add_column_if_not_exists('workspace_members', 'permissions', 'JSONB DEFAULT ''{}''');

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

-- Add missing columns to social_platforms table
SELECT add_column_if_not_exists('social_platforms', 'icon_url', 'TEXT');
SELECT add_column_if_not_exists('social_platforms', 'api_config', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('social_platforms', 'is_active', 'BOOLEAN DEFAULT TRUE');

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

-- Add missing columns to user_social_accounts table
SELECT add_column_if_not_exists('user_social_accounts', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('user_social_accounts', 'platform_id', 'UUID REFERENCES public.social_platforms(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('user_social_accounts', 'access_token', 'TEXT');
SELECT add_column_if_not_exists('user_social_accounts', 'refresh_token', 'TEXT');
SELECT add_column_if_not_exists('user_social_accounts', 'token_expires_at', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('user_social_accounts', 'account_metadata', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('user_social_accounts', 'is_active', 'BOOLEAN DEFAULT TRUE');
SELECT add_column_if_not_exists('user_social_accounts', 'last_used_at', 'TIMESTAMP WITH TIME ZONE');

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

-- Add missing columns to content_posts table
SELECT add_column_if_not_exists('content_posts', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('content_posts', 'title', 'TEXT');
SELECT add_column_if_not_exists('content_posts', 'content_type', 'TEXT DEFAULT ''text'' CHECK (content_type IN (''text'', ''image'', ''video'', ''carousel'', ''story''))');
SELECT add_column_if_not_exists('content_posts', 'status', 'TEXT DEFAULT ''draft'' CHECK (status IN (''draft'', ''scheduled'', ''published'', ''failed'', ''archived''))');
SELECT add_column_if_not_exists('content_posts', 'scheduled_for', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('content_posts', 'published_at', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('content_posts', 'metadata', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('content_posts', 'tags', 'TEXT[] DEFAULT ''{}''');
SELECT add_column_if_not_exists('content_posts', 'updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');

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

-- Add missing columns to content_media table
SELECT add_column_if_not_exists('content_media', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('content_media', 'file_size', 'INTEGER');
SELECT add_column_if_not_exists('content_media', 'mime_type', 'TEXT');
SELECT add_column_if_not_exists('content_media', 'alt_text', 'TEXT');
SELECT add_column_if_not_exists('content_media', 'metadata', 'JSONB DEFAULT ''{}''');

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

-- Add missing columns to post_publications table
SELECT add_column_if_not_exists('post_publications', 'platform_post_id', 'TEXT');
SELECT add_column_if_not_exists('post_publications', 'status', 'TEXT DEFAULT ''pending'' CHECK (status IN (''pending'', ''published'', ''failed'', ''deleted''))');
SELECT add_column_if_not_exists('post_publications', 'published_at', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('post_publications', 'error_message', 'TEXT');
SELECT add_column_if_not_exists('post_publications', 'platform_response', 'JSONB DEFAULT ''{}''');

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

-- Add missing columns to avatar_profiles table
SELECT add_column_if_not_exists('avatar_profiles', 'display_order', 'INTEGER DEFAULT 0');
SELECT add_column_if_not_exists('avatar_profiles', 'is_default', 'BOOLEAN DEFAULT FALSE');
SELECT add_column_if_not_exists('avatar_profiles', 'description', 'TEXT');
SELECT add_column_if_not_exists('avatar_profiles', 'preview_url', 'TEXT');
SELECT add_column_if_not_exists('avatar_profiles', 'avatar_type', 'VARCHAR(20) DEFAULT ''talking_photo'' CHECK (avatar_type IN (''talking_photo'', ''avatar'', ''custom''))');
SELECT add_column_if_not_exists('avatar_profiles', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('avatar_profiles', 'updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');

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

-- Add missing columns to script_generations table
SELECT add_column_if_not_exists('script_generations', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('script_generations', 'target_audience', 'TEXT DEFAULT ''general audience''');
SELECT add_column_if_not_exists('script_generations', 'video_style', 'TEXT DEFAULT ''professional''');
SELECT add_column_if_not_exists('script_generations', 'duration_target', 'INTEGER DEFAULT 60');
SELECT add_column_if_not_exists('script_generations', 'model_used', 'TEXT');
SELECT add_column_if_not_exists('script_generations', 'quality_score', 'FLOAT DEFAULT 0.5 CHECK (quality_score >= 0 AND quality_score <= 1)');
SELECT add_column_if_not_exists('script_generations', 'metadata', 'JSONB DEFAULT ''{}''');

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

-- Add missing columns to video_generations table
SELECT add_column_if_not_exists('video_generations', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('video_generations', 'script_id', 'INTEGER REFERENCES public.script_generations(id) ON DELETE SET NULL');
SELECT add_column_if_not_exists('video_generations', 'profile_id', 'INTEGER REFERENCES public.avatar_profiles(id) ON DELETE SET NULL');
SELECT add_column_if_not_exists('video_generations', 'video_url', 'TEXT');
SELECT add_column_if_not_exists('video_generations', 'thumbnail_url', 'TEXT');
SELECT add_column_if_not_exists('video_generations', 'status', 'VARCHAR(20) DEFAULT ''pending'' CHECK (status IN (''pending'', ''processing'', ''completed'', ''failed'', ''cancelled''))');
SELECT add_column_if_not_exists('video_generations', 'aspect_ratio', 'VARCHAR(20) DEFAULT ''landscape'' CHECK (aspect_ratio IN (''landscape'', ''portrait'', ''square''))');
SELECT add_column_if_not_exists('video_generations', 'duration', 'FLOAT');
SELECT add_column_if_not_exists('video_generations', 'avatar_id', 'VARCHAR(100)');
SELECT add_column_if_not_exists('video_generations', 'voice_id', 'VARCHAR(100)');
SELECT add_column_if_not_exists('video_generations', 'is_public', 'BOOLEAN DEFAULT FALSE');
SELECT add_column_if_not_exists('video_generations', 'metadata', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('video_generations', 'error_message', 'TEXT');
SELECT add_column_if_not_exists('video_generations', 'completed_at', 'TIMESTAMP WITH TIME ZONE');

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

-- Add missing columns to video_analytics table
SELECT add_column_if_not_exists('video_analytics', 'views', 'INTEGER DEFAULT 0');
SELECT add_column_if_not_exists('video_analytics', 'likes', 'INTEGER DEFAULT 0');
SELECT add_column_if_not_exists('video_analytics', 'shares', 'INTEGER DEFAULT 0');
SELECT add_column_if_not_exists('video_analytics', 'comments', 'INTEGER DEFAULT 0');
SELECT add_column_if_not_exists('video_analytics', 'engagement_rate', 'FLOAT DEFAULT 0.0 CHECK (engagement_rate >= 0 AND engagement_rate <= 1)');
SELECT add_column_if_not_exists('video_analytics', 'watch_time_avg', 'FLOAT');
SELECT add_column_if_not_exists('video_analytics', 'completion_rate', 'FLOAT CHECK (completion_rate >= 0 AND completion_rate <= 1)');
SELECT add_column_if_not_exists('video_analytics', 'platform_data', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('video_analytics', 'last_updated', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');

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

-- Add missing columns to user_video_limits table
SELECT add_column_if_not_exists('user_video_limits', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('user_video_limits', 'subscription_tier', 'VARCHAR(20) DEFAULT ''free'' CHECK (subscription_tier IN (''free'', ''starter'', ''creator'', ''creator_pro'', ''enterprise''))');
SELECT add_column_if_not_exists('user_video_limits', 'monthly_limit', 'INTEGER DEFAULT 1');
SELECT add_column_if_not_exists('user_video_limits', 'videos_this_month', 'INTEGER DEFAULT 0');
SELECT add_column_if_not_exists('user_video_limits', 'credits_reset_at', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('user_video_limits', 'is_admin', 'BOOLEAN DEFAULT FALSE');
SELECT add_column_if_not_exists('user_video_limits', 'premium_until', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('user_video_limits', 'metadata', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('user_video_limits', 'updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');

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

-- Add missing columns to avatar_usage_stats table
SELECT add_column_if_not_exists('avatar_usage_stats', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('avatar_usage_stats', 'usage_count', 'INTEGER DEFAULT 0');
SELECT add_column_if_not_exists('avatar_usage_stats', 'total_video_duration', 'FLOAT DEFAULT 0');
SELECT add_column_if_not_exists('avatar_usage_stats', 'avg_quality_score', 'FLOAT DEFAULT 0');
SELECT add_column_if_not_exists('avatar_usage_stats', 'last_used_at', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('avatar_usage_stats', 'updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');

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

-- Add missing columns to workflow_executions table
SELECT add_column_if_not_exists('workflow_executions', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('workflow_executions', 'workflow_config', 'JSONB NOT NULL DEFAULT ''{}''');
SELECT add_column_if_not_exists('workflow_executions', 'tasks', 'TEXT[] DEFAULT ''{}''');
SELECT add_column_if_not_exists('workflow_executions', 'status', 'VARCHAR(50) DEFAULT ''pending'' CHECK (status IN (''pending'', ''running'', ''completed'', ''failed'', ''cancelled''))');
SELECT add_column_if_not_exists('workflow_executions', 'progress', 'FLOAT DEFAULT 0.0 CHECK (progress >= 0 AND progress <= 1)');
SELECT add_column_if_not_exists('workflow_executions', 'started_at', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('workflow_executions', 'completed_at', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('workflow_executions', 'results', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('workflow_executions', 'error_message', 'TEXT');
SELECT add_column_if_not_exists('workflow_executions', 'metadata', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('workflow_executions', 'updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');

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

-- Add missing columns to content_insights table
SELECT add_column_if_not_exists('content_insights', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('content_insights', 'workflow_id', 'UUID REFERENCES public.workflow_executions(id) ON DELETE SET NULL');
SELECT add_column_if_not_exists('content_insights', 'source_url', 'TEXT');
SELECT add_column_if_not_exists('content_insights', 'title', 'TEXT');
SELECT add_column_if_not_exists('content_insights', 'author', 'TEXT');
SELECT add_column_if_not_exists('content_insights', 'engagement_score', 'FLOAT DEFAULT 0');
SELECT add_column_if_not_exists('content_insights', 'sentiment_score', 'FLOAT');
SELECT add_column_if_not_exists('content_insights', 'keywords', 'TEXT[] DEFAULT ''{}''');
SELECT add_column_if_not_exists('content_insights', 'topics', 'TEXT[] DEFAULT ''{}''');
SELECT add_column_if_not_exists('content_insights', 'extracted_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');
SELECT add_column_if_not_exists('content_insights', 'metadata', 'JSONB DEFAULT ''{}''');

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

-- Add missing columns to content_recommendations table
SELECT add_column_if_not_exists('content_recommendations', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('content_recommendations', 'description', 'TEXT');
SELECT add_column_if_not_exists('content_recommendations', 'content_type', 'TEXT DEFAULT ''post'' CHECK (content_type IN (''post'', ''video'', ''story'', ''carousel''))');
SELECT add_column_if_not_exists('content_recommendations', 'recommended_platforms', 'TEXT[] DEFAULT ''{}''');
SELECT add_column_if_not_exists('content_recommendations', 'confidence_score', 'FLOAT DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 1)');
SELECT add_column_if_not_exists('content_recommendations', 'reasoning', 'TEXT');
SELECT add_column_if_not_exists('content_recommendations', 'suggested_content', 'TEXT');
SELECT add_column_if_not_exists('content_recommendations', 'tags', 'TEXT[] DEFAULT ''{}''');
SELECT add_column_if_not_exists('content_recommendations', 'status', 'TEXT DEFAULT ''pending'' CHECK (status IN (''pending'', ''accepted'', ''rejected'', ''implemented''))');
SELECT add_column_if_not_exists('content_recommendations', 'expires_at', 'TIMESTAMP WITH TIME ZONE');
SELECT add_column_if_not_exists('content_recommendations', 'metadata', 'JSONB DEFAULT ''{}''');

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

-- Add missing columns to platform_analytics table
SELECT add_column_if_not_exists('platform_analytics', 'post_id', 'UUID REFERENCES public.content_posts(id) ON DELETE SET NULL');
SELECT add_column_if_not_exists('platform_analytics', 'metric_type', 'TEXT DEFAULT ''count'' CHECK (metric_type IN (''count'', ''rate'', ''duration'', ''percentage''))');
SELECT add_column_if_not_exists('platform_analytics', 'recorded_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()');
SELECT add_column_if_not_exists('platform_analytics', 'metadata', 'JSONB DEFAULT ''{}''');

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

-- Add missing columns to user_activity_logs table
SELECT add_column_if_not_exists('user_activity_logs', 'workspace_id', 'UUID REFERENCES public.workspaces(id) ON DELETE CASCADE');
SELECT add_column_if_not_exists('user_activity_logs', 'resource_type', 'TEXT');
SELECT add_column_if_not_exists('user_activity_logs', 'resource_id', 'TEXT');
SELECT add_column_if_not_exists('user_activity_logs', 'details', 'JSONB DEFAULT ''{}''');
SELECT add_column_if_not_exists('user_activity_logs', 'ip_address', 'INET');
SELECT add_column_if_not_exists('user_activity_logs', 'user_agent', 'TEXT');

-- =====================================================
-- INDEXES FOR PERFORMANCE (SAFE CREATION)
-- =====================================================

-- Core platform indexes
SELECT create_index_if_not_exists('idx_users_email', 'users', '(email)');
SELECT create_index_if_not_exists('idx_users_subscription_tier', 'users', '(subscription_tier)');
SELECT create_index_if_not_exists('idx_workspaces_owner_id', 'workspaces', '(owner_id)');
SELECT create_index_if_not_exists('idx_workspace_members_workspace_id', 'workspace_members', '(workspace_id)');
SELECT create_index_if_not_exists('idx_workspace_members_user_id', 'workspace_members', '(user_id)');

-- Social media indexes
SELECT create_index_if_not_exists('idx_user_social_accounts_user_id', 'user_social_accounts', '(user_id)');
SELECT create_index_if_not_exists('idx_user_social_accounts_workspace_id', 'user_social_accounts', '(workspace_id)');
SELECT create_index_if_not_exists('idx_user_social_accounts_platform_id', 'user_social_accounts', '(platform_id)');

-- Content indexes
SELECT create_index_if_not_exists('idx_content_posts_workspace_id', 'content_posts', '(workspace_id)');
SELECT create_index_if_not_exists('idx_content_posts_user_id', 'content_posts', '(user_id)');
SELECT create_index_if_not_exists('idx_content_posts_status', 'content_posts', '(status)');
SELECT create_index_if_not_exists('idx_content_posts_scheduled_for', 'content_posts', '(scheduled_for)');
SELECT create_index_if_not_exists('idx_content_posts_created_at', 'content_posts', '(created_at DESC)');
SELECT create_index_if_not_exists('idx_content_media_post_id', 'content_media', '(post_id)');
SELECT create_index_if_not_exists('idx_post_publications_post_id', 'post_publications', '(post_id)');
SELECT create_index_if_not_exists('idx_post_publications_account_id', 'post_publications', '(account_id)');

-- Avatar system indexes
SELECT create_index_if_not_exists('idx_avatar_profiles_workspace_id', 'avatar_profiles', '(workspace_id)');
SELECT create_index_if_not_exists('idx_avatar_profiles_display_order', 'avatar_profiles', '(display_order)');
SELECT create_index_if_not_exists('idx_avatar_profiles_avatar_id', 'avatar_profiles', '(avatar_id)');
SELECT create_index_if_not_exists('idx_avatar_profiles_is_default', 'avatar_profiles', '(is_default)');
SELECT create_index_if_not_exists('idx_script_generations_user_id', 'script_generations', '(user_id)');
SELECT create_index_if_not_exists('idx_script_generations_workspace_id', 'script_generations', '(workspace_id)');
SELECT create_index_if_not_exists('idx_script_generations_created_at', 'script_generations', '(created_at DESC)');
SELECT create_index_if_not_exists('idx_video_generations_user_id', 'video_generations', '(user_id)');
SELECT create_index_if_not_exists('idx_video_generations_workspace_id', 'video_generations', '(workspace_id)');
SELECT create_index_if_not_exists('idx_video_generations_status', 'video_generations', '(status)');
SELECT create_index_if_not_exists('idx_video_generations_heygen_id', 'video_generations', '(heygen_video_id)');
SELECT create_index_if_not_exists('idx_video_analytics_video_id', 'video_analytics', '(video_id)');
SELECT create_index_if_not_exists('idx_user_video_limits_user_id', 'user_video_limits', '(user_id)');

-- Research & workflow indexes
SELECT create_index_if_not_exists('idx_workflow_executions_workspace_id', 'workflow_executions', '(workspace_id)');
SELECT create_index_if_not_exists('idx_workflow_executions_user_id', 'workflow_executions', '(user_id)');
SELECT create_index_if_not_exists('idx_workflow_executions_status', 'workflow_executions', '(status)');
SELECT create_index_if_not_exists('idx_content_insights_workspace_id', 'content_insights', '(workspace_id)');
SELECT create_index_if_not_exists('idx_content_insights_workflow_id', 'content_insights', '(workflow_id)');
SELECT create_index_if_not_exists('idx_content_recommendations_workspace_id', 'content_recommendations', '(workspace_id)');
SELECT create_index_if_not_exists('idx_content_recommendations_status', 'content_recommendations', '(status)');

-- Analytics indexes
SELECT create_index_if_not_exists('idx_platform_analytics_account_id', 'platform_analytics', '(account_id)');
SELECT create_index_if_not_exists('idx_platform_analytics_post_id', 'platform_analytics', '(post_id)');
SELECT create_index_if_not_exists('idx_platform_analytics_recorded_at', 'platform_analytics', '(recorded_at DESC)');
SELECT create_index_if_not_exists('idx_user_activity_logs_user_id', 'user_activity_logs', '(user_id)');
SELECT create_index_if_not_exists('idx_user_activity_logs_workspace_id', 'user_activity_logs', '(workspace_id)');
SELECT create_index_if_not_exists('idx_user_activity_logs_created_at', 'user_activity_logs', '(created_at DESC)');

-- =====================================================
-- TRIGGERS FOR UPDATED_AT COLUMNS (SAFE CREATION)
-- =====================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns (safe creation)
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
-- UTILITY FUNCTIONS (SAFE CREATION)
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
-- INITIAL DATA SETUP (SAFE INSERTION)
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
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    icon_url = EXCLUDED.icon_url,
    is_active = EXCLUDED.is_active;

-- Insert default avatar profiles (only if none exist)
INSERT INTO public.avatar_profiles (name, avatar_id, voice_id, display_order, is_default, description, avatar_type) 
SELECT * FROM (VALUES
    ('Professional Male', 'default_male_avatar', 'default_male_voice', 0, TRUE, 'Professional male avatar suitable for business content', 'avatar'),
    ('Professional Female', 'default_female_avatar', 'default_female_voice', 1, FALSE, 'Professional female avatar suitable for business content', 'avatar'),
    ('Casual Male', 'casual_male_avatar', 'casual_male_voice', 2, FALSE, 'Casual male avatar for informal content', 'talking_photo'),
    ('Casual Female', 'casual_female_avatar', 'casual_female_voice', 3, FALSE, 'Casual female avatar for informal content', 'talking_photo')
) AS new_avatars(name, avatar_id, voice_id, display_order, is_default, description, avatar_type)
WHERE NOT EXISTS (SELECT 1 FROM public.avatar_profiles LIMIT 1);

-- =====================================================
-- CLEANUP UTILITY FUNCTIONS
-- =====================================================

-- Drop the utility functions we created for this migration
DROP FUNCTION IF EXISTS add_column_if_not_exists(TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS create_index_if_not_exists(TEXT, TEXT, TEXT);

-- =====================================================
-- SCHEMA MIGRATION COMPLETE
-- =====================================================

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✅ Incremental schema migration completed successfully!';
    RAISE NOTICE '📊 All tables created or updated with missing columns';
    RAISE NOTICE '🔍 All indexes created safely';
    RAISE NOTICE '⚡ All triggers and functions updated';
    RAISE NOTICE '📝 Initial data inserted or updated';
    RAISE NOTICE '🎯 Schema is ready for Sentigen Social platform';
END
$$;
