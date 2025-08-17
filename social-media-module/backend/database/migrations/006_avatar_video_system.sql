-- Avatar Video Generation System Database Schema
-- Integrates with existing research tools and user system

-- Avatar Profiles Table
CREATE TABLE IF NOT EXISTS avatar_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,                    -- Display name (e.g., "Brody", "Sarah")
    avatar_id VARCHAR(100) NOT NULL,               -- HeyGen avatar/talking_photo ID
    voice_id VARCHAR(100) NOT NULL,                -- HeyGen voice ID
    display_order INTEGER DEFAULT 0,               -- Order in carousel
    is_default BOOLEAN DEFAULT FALSE,              -- Default avatar flag
    description TEXT,                              -- Avatar description
    preview_url TEXT,                              -- Local video preview URL
    avatar_type VARCHAR(20) DEFAULT 'talking_photo', -- 'talking_photo' or 'avatar'
    gender VARCHAR(20),                            -- 'male', 'female', 'neutral'
    age_range VARCHAR(20),                         -- 'young', 'middle', 'senior'
    style VARCHAR(50),                             -- 'professional', 'casual', 'energetic'
    language_code VARCHAR(10) DEFAULT 'en',       -- Primary language
    is_active BOOLEAN DEFAULT TRUE,                -- Active/inactive status
    subscription_tier VARCHAR(20) DEFAULT 'free', -- 'free', 'pro', 'enterprise'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video Generations Table
CREATE TABLE IF NOT EXISTS video_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,

    -- Content source tracking
    research_job_id UUID REFERENCES research_jobs(id) ON DELETE SET NULL,
    content_source VARCHAR(50),                    -- 'research', 'manual', 'imported'
    source_tool VARCHAR(50),                       -- 'reddit', 'hackernews', 'github', 'google_trends'

    -- Script and content
    script_title VARCHAR(200),
    script_content TEXT NOT NULL,
    original_content JSONB,                        -- Original research data if applicable

    -- Avatar and generation settings
    profile_id UUID REFERENCES avatar_profiles(id) ON DELETE SET NULL,
    heygen_video_id VARCHAR(100) NOT NULL,         -- HeyGen's video ID
    video_url TEXT,                                -- Final video URL
    thumbnail_url TEXT,                            -- Video thumbnail

    -- Status and metadata
    status VARCHAR(20) DEFAULT 'processing',       -- 'processing', 'completed', 'failed', 'error'
    aspect_ratio VARCHAR(20) DEFAULT 'portrait',   -- 'portrait', 'landscape', 'square'
    duration_seconds INTEGER,                      -- Video duration
    file_size_bytes BIGINT,                        -- File size

    -- Generation settings
    voice_speed DECIMAL(3,2) DEFAULT 1.0,         -- Voice speed multiplier
    enable_captions BOOLEAN DEFAULT TRUE,          -- Enable subtitles
    background_color VARCHAR(7) DEFAULT '#ffffff', -- Background color
    background_type VARCHAR(20) DEFAULT 'color',   -- 'color', 'image', 'video'
    background_url TEXT,                           -- Background asset URL

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Analytics
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,

    -- IP tracking for non-authenticated users
    ip_address INET,
    user_agent TEXT
);

-- Video Templates Table (for reusable video configurations)
CREATE TABLE IF NOT EXISTS video_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Template settings
    default_profile_id UUID REFERENCES avatar_profiles(id) ON DELETE SET NULL,
    aspect_ratio VARCHAR(20) DEFAULT 'portrait',
    voice_speed DECIMAL(3,2) DEFAULT 1.0,
    enable_captions BOOLEAN DEFAULT TRUE,
    background_settings JSONB,                     -- Background configuration

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,               -- Public template sharing

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Automated Video Campaigns Table (for auto-posting)
CREATE TABLE IF NOT EXISTS video_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Research integration
    research_config_id UUID REFERENCES research_configurations(id) ON DELETE CASCADE,
    source_tools TEXT[] DEFAULT '{}',              -- Array of research tools to use

    -- Video generation settings
    template_id UUID REFERENCES video_templates(id) ON DELETE SET NULL,
    profile_id UUID REFERENCES avatar_profiles(id) ON DELETE SET NULL,

    -- Automation settings
    is_active BOOLEAN DEFAULT TRUE,
    frequency VARCHAR(20) DEFAULT 'daily',         -- 'hourly', 'daily', 'weekly'
    max_videos_per_day INTEGER DEFAULT 3,

    -- Content filtering
    min_content_score INTEGER DEFAULT 70,          -- Minimum content quality score
    content_filters JSONB,                         -- Content filtering rules

    -- Auto-posting settings
    auto_post_enabled BOOLEAN DEFAULT FALSE,
    post_platforms TEXT[] DEFAULT '{}',            -- ['tiktok', 'instagram', 'youtube']
    post_schedule JSONB,                           -- Posting schedule configuration

    -- Status
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    total_videos_generated INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video Analytics Table
CREATE TABLE IF NOT EXISTS video_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES video_generations(id) ON DELETE CASCADE,

    -- Event tracking
    event_type VARCHAR(50) NOT NULL,               -- 'view', 'download', 'share', 'like'
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- User context
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,

    -- Platform tracking (for auto-posted videos)
    platform VARCHAR(50),                          -- 'tiktok', 'instagram', 'youtube'
    platform_video_id VARCHAR(100),               -- Platform-specific video ID

    -- Metadata
    metadata JSONB
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_active ON avatar_profiles(is_active, display_order);
CREATE INDEX IF NOT EXISTS idx_avatar_profiles_tier ON avatar_profiles(subscription_tier, is_active);
CREATE INDEX IF NOT EXISTS idx_video_generations_user ON video_generations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_generations_status ON video_generations(status, created_at);
CREATE INDEX IF NOT EXISTS idx_video_generations_research ON video_generations(research_job_id, source_tool);
CREATE INDEX IF NOT EXISTS idx_video_campaigns_active ON video_campaigns(is_active, next_run_at);
CREATE INDEX IF NOT EXISTS idx_video_analytics_video ON video_analytics(video_id, event_type, event_timestamp);

-- Row Level Security (RLS) Policies
ALTER TABLE avatar_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_analytics ENABLE ROW LEVEL SECURITY;

-- Avatar profiles are globally readable, admin writable
CREATE POLICY avatar_profiles_read ON avatar_profiles FOR SELECT USING (is_active = true);
CREATE POLICY avatar_profiles_admin ON avatar_profiles FOR ALL USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.is_admin = true)
);

-- Video generations are user-specific
CREATE POLICY video_generations_user ON video_generations FOR ALL USING (
    user_id = auth.uid() OR
    EXISTS (
        SELECT 1 FROM workspace_members
        WHERE workspace_members.workspace_id = video_generations.workspace_id
        AND workspace_members.user_id = auth.uid()
    )
);

-- Video templates are user/workspace specific
CREATE POLICY video_templates_user ON video_templates FOR ALL USING (
    user_id = auth.uid() OR
    (is_public = true AND current_setting('request.method') = 'GET') OR
    EXISTS (
        SELECT 1 FROM workspace_members
        WHERE workspace_members.workspace_id = video_templates.workspace_id
        AND workspace_members.user_id = auth.uid()
    )
);

-- Video campaigns are user/workspace specific
CREATE POLICY video_campaigns_user ON video_campaigns FOR ALL USING (
    user_id = auth.uid() OR
    EXISTS (
        SELECT 1 FROM workspace_members
        WHERE workspace_members.workspace_id = video_campaigns.workspace_id
        AND workspace_members.user_id = auth.uid()
    )
);

-- Video analytics are readable by video owner
CREATE POLICY video_analytics_read ON video_analytics FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM video_generations
        WHERE video_generations.id = video_analytics.video_id
        AND (
            video_generations.user_id = auth.uid() OR
            EXISTS (
                SELECT 1 FROM workspace_members
                WHERE workspace_members.workspace_id = video_generations.workspace_id
                AND workspace_members.user_id = auth.uid()
            )
        )
    )
);

-- Insert default avatar profiles
INSERT INTO avatar_profiles (name, avatar_id, voice_id, description, display_order, avatar_type, gender, age_range, style, subscription_tier) VALUES
-- Free tier avatars
('Sarah', 'a58345668aa2444c8229923ef67a3e76', 'b54cd1be94d848879a0acd2f7138fd3c', 'Professional and articulate presenter', 1, 'talking_photo', 'female', 'young', 'professional', 'free'),
('Mike', '4906bbce5e1a49d9936a59403c2c8efe', '05a6438db65442b0bbe31526e5fe8d80', 'Confident and charismatic presenter', 2, 'avatar', 'male', 'middle', 'professional', 'free'),
('Emma', 'c8d7e9f1a2b3c4d5e6f7g8h9i0j1k2l3', 'f1e2d3c4b5a6978869504132875643ab', 'Friendly and approachable presenter', 3, 'talking_photo', 'female', 'young', 'casual', 'free'),

-- Pro tier avatars
('David', 'm4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9', 'g2f3e4d5c6b7a8958675041328756432', 'Executive-level professional presenter', 4, 'avatar', 'male', 'middle', 'professional', 'pro'),
('Lisa', 'c9d8e7f6g5h4i3j2k1l0m9n8o7p6q5r4', 'h3g4f5e6d7c8b9a0586750413287564', 'Dynamic and energetic presenter', 5, 'talking_photo', 'female', 'middle', 'energetic', 'pro'),
('James', 's3t4u5v6w7x8y9z0a1b2c3d4e5f6g7h8', 'i4h5g6f7e8d9c0b1a2586750413287565', 'Authoritative and trustworthy presenter', 6, 'avatar', 'male', 'senior', 'professional', 'pro'),

-- Enterprise tier avatars
('Sophia', 'i7j8k9l0m1n2o3p4q5r6s7t8u9v0w1x2', 'j5i6h7g8f9e0d1c2b3586750413287566', 'Sophisticated executive presenter', 7, 'talking_photo', 'female', 'middle', 'professional', 'enterprise'),
('Alexander', 'y3z4a5b6c7d8e9f0g1h2i3j4k5l6m7n8', 'k6j7i8h9g0f1e2d3c4586750413287567', 'Distinguished senior executive', 8, 'avatar', 'male', 'senior', 'professional', 'enterprise')

ON CONFLICT (avatar_id) DO NOTHING;

-- Set one avatar as default
UPDATE avatar_profiles SET is_default = true WHERE name = 'Sarah' AND is_default = false;

-- Create default video template
INSERT INTO video_templates (name, description, aspect_ratio, background_settings) VALUES
('Default Portrait', 'Standard portrait video template for social media', 'portrait', '{"type": "color", "value": "#ffffff"}'),
('Default Landscape', 'Standard landscape video template for presentations', 'landscape', '{"type": "color", "value": "#f8f9fa"}'),
('Professional', 'Professional template with subtle background', 'portrait', '{"type": "gradient", "colors": ["#667eea", "#764ba2"]}')
ON CONFLICT DO NOTHING;
