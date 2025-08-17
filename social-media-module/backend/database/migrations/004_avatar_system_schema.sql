-- Avatar System Database Schema Migration
-- Creates tables for avatar profiles, script generation, and video creation
-- Integrated from TikClip functionality

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Avatar Profiles Table
CREATE TABLE IF NOT EXISTS avatar_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    avatar_id VARCHAR(100) NOT NULL,
    voice_id VARCHAR(100) NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    description TEXT,
    preview_url TEXT,
    avatar_type VARCHAR(20) DEFAULT 'talking_photo' CHECK (avatar_type IN ('talking_photo', 'avatar', 'custom')),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for avatar_profiles
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_workspace_id ON avatar_profiles(workspace_id);
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_display_order ON avatar_profiles(display_order);
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_avatar_id ON avatar_profiles(avatar_id);
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_is_default ON avatar_profiles(is_default);

-- Script Generations Table
CREATE TABLE IF NOT EXISTS script_generations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
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

-- Indexes for script_generations
CREATE INDEX IF NOT EXISTS idx_script_generations_user_id ON script_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_script_generations_workspace_id ON script_generations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_script_generations_created_at ON script_generations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_script_generations_topic ON script_generations(topic);
CREATE INDEX IF NOT EXISTS idx_script_generations_quality_score ON script_generations(quality_score DESC);

-- Video Generations Table
CREATE TABLE IF NOT EXISTS video_generations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    script_id INTEGER REFERENCES script_generations(id) ON DELETE SET NULL,
    profile_id INTEGER REFERENCES avatar_profiles(id) ON DELETE SET NULL,
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

-- Indexes for video_generations
CREATE INDEX IF NOT EXISTS idx_video_generations_user_id ON video_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_video_generations_workspace_id ON video_generations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_video_generations_status ON video_generations(status);
CREATE INDEX IF NOT EXISTS idx_video_generations_heygen_id ON video_generations(heygen_video_id);
CREATE INDEX IF NOT EXISTS idx_video_generations_created_at ON video_generations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_generations_script_id ON video_generations(script_id);
CREATE INDEX IF NOT EXISTS idx_video_generations_profile_id ON video_generations(profile_id);

-- Video Analytics Table
CREATE TABLE IF NOT EXISTS video_analytics (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES video_generations(id) ON DELETE CASCADE,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0 CHECK (engagement_rate >= 0 AND engagement_rate <= 1),
    watch_time_avg FLOAT, -- Average watch time in seconds
    completion_rate FLOAT CHECK (completion_rate >= 0 AND completion_rate <= 1), -- Percentage of video watched
    platform_data JSONB DEFAULT '{}', -- Platform-specific analytics
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for video_analytics
CREATE INDEX IF NOT EXISTS idx_video_analytics_video_id ON video_analytics(video_id);
CREATE INDEX IF NOT EXISTS idx_video_analytics_last_updated ON video_analytics(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_video_analytics_engagement_rate ON video_analytics(engagement_rate DESC);

-- User Video Limits Table (for subscription management)
CREATE TABLE IF NOT EXISTS user_video_limits (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
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

-- Indexes for user_video_limits
CREATE INDEX IF NOT EXISTS idx_user_video_limits_user_id ON user_video_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_video_limits_workspace_id ON user_video_limits(workspace_id);
CREATE INDEX IF NOT EXISTS idx_user_video_limits_subscription_tier ON user_video_limits(subscription_tier);

-- Avatar Usage Statistics Table
CREATE TABLE IF NOT EXISTS avatar_usage_stats (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES avatar_profiles(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    usage_count INTEGER DEFAULT 0,
    total_video_duration FLOAT DEFAULT 0, -- Total duration of videos created with this avatar
    avg_quality_score FLOAT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for avatar_usage_stats
CREATE INDEX IF NOT EXISTS idx_avatar_usage_stats_profile_id ON avatar_usage_stats(profile_id);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_stats_workspace_id ON avatar_usage_stats(workspace_id);
CREATE INDEX IF NOT EXISTS idx_avatar_usage_stats_usage_count ON avatar_usage_stats(usage_count DESC);

-- Update trigger function (reuse existing one or create if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to tables with updated_at columns
DO $$
BEGIN
    -- avatar_profiles trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_avatar_profiles_updated_at') THEN
        CREATE TRIGGER update_avatar_profiles_updated_at
        BEFORE UPDATE ON avatar_profiles
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- user_video_limits trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_user_video_limits_updated_at') THEN
        CREATE TRIGGER update_user_video_limits_updated_at
        BEFORE UPDATE ON user_video_limits
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- avatar_usage_stats trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_avatar_usage_stats_updated_at') THEN
        CREATE TRIGGER update_avatar_usage_stats_updated_at
        BEFORE UPDATE ON avatar_usage_stats
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;

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
    -- Reset credits for users whose reset date has passed
    UPDATE user_video_limits 
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

-- Function to check and update video limits
CREATE OR REPLACE FUNCTION check_video_creation_limit(p_user_id UUID, p_workspace_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_limits RECORD;
    can_create BOOLEAN := FALSE;
BEGIN
    -- Get or create user limits record
    SELECT * INTO user_limits 
    FROM user_video_limits 
    WHERE user_id = p_user_id;
    
    -- If no record exists, create one with free tier defaults
    IF NOT FOUND THEN
        INSERT INTO user_video_limits (user_id, workspace_id, subscription_tier, monthly_limit, videos_this_month, credits_reset_at)
        VALUES (p_user_id, p_workspace_id, 'free', 1, 0, DATE_TRUNC('month', NOW()) + INTERVAL '1 month')
        RETURNING * INTO user_limits;
    END IF;
    
    -- Reset credits if needed
    PERFORM reset_monthly_video_credits();
    
    -- Refresh the record after potential reset
    SELECT * INTO user_limits 
    FROM user_video_limits 
    WHERE user_id = p_user_id;
    
    -- Check if user can create video
    IF user_limits.is_admin THEN
        can_create := TRUE;
    ELSIF user_limits.videos_this_month < user_limits.monthly_limit THEN
        can_create := TRUE;
        -- Increment the counter
        UPDATE user_video_limits 
        SET videos_this_month = videos_this_month + 1,
            updated_at = NOW()
        WHERE user_id = p_user_id;
    END IF;
    
    RETURN can_create;
END;
$$ LANGUAGE plpgsql;

-- Function to update avatar usage statistics
CREATE OR REPLACE FUNCTION update_avatar_usage_stats(p_profile_id INTEGER, p_workspace_id UUID, p_video_duration FLOAT DEFAULT NULL, p_quality_score FLOAT DEFAULT NULL)
RETURNS void AS $$
BEGIN
    -- Insert or update avatar usage statistics
    INSERT INTO avatar_usage_stats (profile_id, workspace_id, usage_count, total_video_duration, avg_quality_score, last_used_at)
    VALUES (p_profile_id, p_workspace_id, 1, COALESCE(p_video_duration, 0), COALESCE(p_quality_score, 0), NOW())
    ON CONFLICT (profile_id) DO UPDATE SET
        usage_count = avatar_usage_stats.usage_count + 1,
        total_video_duration = avatar_usage_stats.total_video_duration + COALESCE(p_video_duration, 0),
        avg_quality_score = CASE 
            WHEN p_quality_score IS NOT NULL THEN 
                (avatar_usage_stats.avg_quality_score * (avatar_usage_stats.usage_count - 1) + p_quality_score) / avatar_usage_stats.usage_count
            ELSE avatar_usage_stats.avg_quality_score
        END,
        last_used_at = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Insert default avatar profiles (if none exist)
DO $$
BEGIN
    -- Only insert if no avatar profiles exist
    IF NOT EXISTS (SELECT 1 FROM avatar_profiles LIMIT 1) THEN
        -- Insert some default avatar profiles
        -- Note: These are placeholder values - replace with actual HeyGen avatar/voice IDs
        INSERT INTO avatar_profiles (name, avatar_id, voice_id, display_order, is_default, description, avatar_type) VALUES
        ('Professional Male', 'default_male_avatar', 'default_male_voice', 0, TRUE, 'Professional male avatar suitable for business content', 'avatar'),
        ('Professional Female', 'default_female_avatar', 'default_female_voice', 1, FALSE, 'Professional female avatar suitable for business content', 'avatar'),
        ('Casual Male', 'casual_male_avatar', 'casual_male_voice', 2, FALSE, 'Casual male avatar for informal content', 'talking_photo'),
        ('Casual Female', 'casual_female_avatar', 'casual_female_voice', 3, FALSE, 'Casual female avatar for informal content', 'talking_photo');
        
        RAISE NOTICE 'Inserted default avatar profiles';
    END IF;
END
$$;

-- Create indexes for better performance on common queries
CREATE INDEX IF NOT EXISTS idx_script_generations_user_workspace_created ON script_generations(user_id, workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_generations_user_workspace_status ON video_generations(user_id, workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_video_generations_status_created ON video_generations(status, created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE avatar_profiles IS 'Stores avatar profile configurations for video generation';
COMMENT ON TABLE script_generations IS 'Stores AI-generated scripts for video content';
COMMENT ON TABLE video_generations IS 'Tracks video generation requests and their status';
COMMENT ON TABLE video_analytics IS 'Stores performance analytics for generated videos';
COMMENT ON TABLE user_video_limits IS 'Manages user subscription limits and video credits';
COMMENT ON TABLE avatar_usage_stats IS 'Tracks usage statistics for avatar profiles';

COMMENT ON COLUMN avatar_profiles.avatar_id IS 'HeyGen avatar identifier';
COMMENT ON COLUMN avatar_profiles.voice_id IS 'HeyGen voice identifier';
COMMENT ON COLUMN script_generations.quality_score IS 'AI-calculated quality score (0-1)';
COMMENT ON COLUMN video_generations.heygen_video_id IS 'HeyGen video generation job identifier';
COMMENT ON COLUMN user_video_limits.subscription_tier IS 'User subscription level determining video limits';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
