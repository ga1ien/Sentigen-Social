-- Dashboard Analytics Tables
-- For real-time dashboard data

-- Analytics table for tracking user metrics
CREATE TABLE IF NOT EXISTS analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    total_reach INTEGER DEFAULT 0,
    reach_change DECIMAL(5,2) DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0,
    engagement_change DECIMAL(5,2) DEFAULT 0,
    new_followers INTEGER DEFAULT 0,
    followers_change DECIMAL(5,2) DEFAULT 0,
    content_count INTEGER DEFAULT 0,
    period_start TIMESTAMP WITH TIME ZONE DEFAULT NOW() - INTERVAL '7 days',
    period_end TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Suggestions table
CREATE TABLE IF NOT EXISTS ai_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'trending_topic', 'best_time', 'content_idea'
    title VARCHAR(255),
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scheduled Posts table (if not exists)
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    post_id UUID REFERENCES social_media_posts(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'published', 'failed', 'cancelled'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add engagement_count to social_media_posts if not exists
ALTER TABLE social_media_posts
ADD COLUMN IF NOT EXISTS engagement_count INTEGER DEFAULT 0;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_analytics_user_created ON analytics(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_suggestions_user_active ON ai_suggestions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_scheduled_user_status ON scheduled_posts(user_id, status, scheduled_time);

-- Enable RLS
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_posts ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own analytics" ON analytics
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analytics" ON analytics
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own analytics" ON analytics
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own suggestions" ON ai_suggestions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own scheduled posts" ON scheduled_posts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own scheduled posts" ON scheduled_posts
    FOR ALL USING (auth.uid() = user_id);

-- Function to generate sample analytics data for new users
CREATE OR REPLACE FUNCTION generate_initial_analytics()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert initial analytics row for new user
    INSERT INTO analytics (
        user_id,
        total_reach,
        reach_change,
        engagement_rate,
        engagement_change,
        new_followers,
        followers_change,
        content_count
    ) VALUES (
        NEW.id,
        0,
        0,
        0,
        0,
        0,
        0,
        0
    );

    -- Insert welcome suggestions
    INSERT INTO ai_suggestions (user_id, type, title, description) VALUES
    (NEW.id, 'getting_started', 'Welcome to zyyn', 'Start by creating your first post to unlock personalized AI suggestions'),
    (NEW.id, 'best_time', 'Best posting time', 'Based on your timezone, try posting between 9 AM and 11 AM for maximum engagement'),
    (NEW.id, 'content_idea', 'First post idea', 'Introduce yourself and share what you''re excited to create');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for new user analytics
DROP TRIGGER IF EXISTS create_user_analytics ON auth.users;
CREATE TRIGGER create_user_analytics
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION generate_initial_analytics();
