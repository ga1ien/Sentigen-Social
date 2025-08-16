-- Initial database schema for Social Media Module
-- Compatible with Supabase and pgvector

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Social media posts table
CREATE TABLE IF NOT EXISTS social_media_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    platforms TEXT[] DEFAULT '{}',
    media_urls TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    ayrshare_post_id VARCHAR(255),
    platform_results JSONB DEFAULT '{}',
    analytics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Worker tasks table
CREATE TABLE IF NOT EXISTS worker_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    worker_type VARCHAR(100) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Worker results table
CREATE TABLE IF NOT EXISTS worker_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES worker_tasks(id) ON DELETE CASCADE,
    worker_type VARCHAR(100) NOT NULL,
    result_data JSONB NOT NULL DEFAULT '{}',
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Media assets table
CREATE TABLE IF NOT EXISTS media_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_type VARCHAR(100) NOT NULL,
    file_size INTEGER,
    storage_url TEXT NOT NULL,
    thumbnail_url TEXT,
    width INTEGER,
    height INTEGER,
    duration_seconds INTEGER,
    generated_by VARCHAR(100), -- midjourney, heygen, veo3, etc.
    generation_params JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content embeddings table (for semantic search)
CREATE TABLE IF NOT EXISTS content_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    content_type VARCHAR(100) NOT NULL, -- post, media, task, etc.
    content_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    post_id UUID REFERENCES social_media_posts(id) ON DELETE CASCADE,
    task_id UUID REFERENCES worker_tasks(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_workspaces_owner_id ON workspaces(owner_id);
CREATE INDEX IF NOT EXISTS idx_social_media_posts_workspace_id ON social_media_posts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_social_media_posts_user_id ON social_media_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_social_media_posts_status ON social_media_posts(status);
CREATE INDEX IF NOT EXISTS idx_social_media_posts_scheduled_at ON social_media_posts(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_social_media_posts_created_at ON social_media_posts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_worker_tasks_workspace_id ON worker_tasks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_worker_tasks_user_id ON worker_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_worker_tasks_status ON worker_tasks(status);
CREATE INDEX IF NOT EXISTS idx_worker_tasks_worker_type ON worker_tasks(worker_type);
CREATE INDEX IF NOT EXISTS idx_worker_tasks_scheduled_at ON worker_tasks(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_worker_tasks_created_at ON worker_tasks(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_worker_results_task_id ON worker_results(task_id);
CREATE INDEX IF NOT EXISTS idx_worker_results_worker_type ON worker_results(worker_type);
CREATE INDEX IF NOT EXISTS idx_worker_results_created_at ON worker_results(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_media_assets_workspace_id ON media_assets(workspace_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_user_id ON media_assets(user_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_file_type ON media_assets(file_type);
CREATE INDEX IF NOT EXISTS idx_media_assets_generated_by ON media_assets(generated_by);
CREATE INDEX IF NOT EXISTS idx_media_assets_created_at ON media_assets(created_at DESC);

-- Vector indexes for semantic search
CREATE INDEX IF NOT EXISTS idx_content_embeddings_workspace_id ON content_embeddings(workspace_id);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_content_type ON content_embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_content_id ON content_embeddings(content_id);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_vector 
    ON content_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Metadata indexes (GIN for JSONB)
CREATE INDEX IF NOT EXISTS idx_workspaces_metadata ON workspaces USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_social_media_posts_metadata ON social_media_posts USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_social_media_posts_platform_results ON social_media_posts USING gin (platform_results);
CREATE INDEX IF NOT EXISTS idx_worker_tasks_metadata ON worker_tasks USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_worker_results_metadata ON worker_results USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_media_assets_metadata ON media_assets USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_metadata ON content_embeddings USING gin (metadata);

CREATE INDEX IF NOT EXISTS idx_analytics_events_workspace_id ON analytics_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_events_data ON analytics_events USING gin (event_data);

-- Row Level Security (RLS) policies for Supabase
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_media_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (users can only access their own data)
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own workspaces" ON workspaces FOR SELECT USING (auth.uid() = owner_id);
CREATE POLICY "Users can create workspaces" ON workspaces FOR INSERT WITH CHECK (auth.uid() = owner_id);
CREATE POLICY "Users can update own workspaces" ON workspaces FOR UPDATE USING (auth.uid() = owner_id);
CREATE POLICY "Users can delete own workspaces" ON workspaces FOR DELETE USING (auth.uid() = owner_id);

CREATE POLICY "Users can view workspace posts" ON social_media_posts FOR SELECT 
    USING (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));
CREATE POLICY "Users can create workspace posts" ON social_media_posts FOR INSERT 
    WITH CHECK (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));
CREATE POLICY "Users can update workspace posts" ON social_media_posts FOR UPDATE 
    USING (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));
CREATE POLICY "Users can delete workspace posts" ON social_media_posts FOR DELETE 
    USING (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));

-- Similar policies for other tables
CREATE POLICY "Users can view workspace tasks" ON worker_tasks FOR SELECT 
    USING (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));
CREATE POLICY "Users can create workspace tasks" ON worker_tasks FOR INSERT 
    WITH CHECK (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));
CREATE POLICY "Users can update workspace tasks" ON worker_tasks FOR UPDATE 
    USING (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));

CREATE POLICY "Users can view task results" ON worker_results FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM worker_tasks 
        JOIN workspaces ON workspaces.id = worker_tasks.workspace_id 
        WHERE worker_tasks.id = task_id AND workspaces.owner_id = auth.uid()
    ));

CREATE POLICY "Users can view workspace media" ON media_assets FOR SELECT 
    USING (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));
CREATE POLICY "Users can create workspace media" ON media_assets FOR INSERT 
    WITH CHECK (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));

CREATE POLICY "Users can view workspace embeddings" ON content_embeddings FOR SELECT 
    USING (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));
CREATE POLICY "Users can create workspace embeddings" ON content_embeddings FOR INSERT 
    WITH CHECK (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));

CREATE POLICY "Users can view workspace analytics" ON analytics_events FOR SELECT 
    USING (EXISTS (SELECT 1 FROM workspaces WHERE workspaces.id = workspace_id AND workspaces.owner_id = auth.uid()));

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_social_media_posts_updated_at BEFORE UPDATE ON social_media_posts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_worker_tasks_updated_at BEFORE UPDATE ON worker_tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_media_assets_updated_at BEFORE UPDATE ON media_assets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_embeddings_updated_at BEFORE UPDATE ON content_embeddings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default workspace for new users (optional)
CREATE OR REPLACE FUNCTION create_default_workspace()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO workspaces (name, description, owner_id, metadata)
    VALUES (
        'My Workspace',
        'Default workspace for social media management',
        NEW.id,
        '{"is_default": true}'
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER create_user_default_workspace 
    AFTER INSERT ON users 
    FOR EACH ROW EXECUTE FUNCTION create_default_workspace();
