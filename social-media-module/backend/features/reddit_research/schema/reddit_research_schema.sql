-- Reddit Research Feature Schema
-- Flexible schema that works with any research topic
-- Created: 2025-01-16
-- Status: DEPLOYED ✅

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Research Sessions Table
-- Tracks individual research sessions for any topic
CREATE TABLE IF NOT EXISTS public.reddit_research_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL,
    user_id UUID NOT NULL,
    session_name TEXT NOT NULL,
    search_query TEXT NOT NULL,
    research_topic TEXT,
    target_subreddits TEXT[],
    max_posts_per_subreddit INTEGER DEFAULT 10,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    total_posts_found INTEGER DEFAULT 0,
    total_comments_found INTEGER DEFAULT 0,
    session_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Reddit Content Table (Posts + Comments)
-- Unified table for both posts and comments with flexible structure
CREATE TABLE IF NOT EXISTS public.reddit_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES public.reddit_research_sessions(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL,
    parent_id UUID, -- For comments, references the parent post
    reddit_id TEXT NOT NULL, -- Reddit's internal ID
    content_type TEXT NOT NULL CHECK (content_type IN ('post', 'comment')),

    -- Basic Reddit Data
    subreddit TEXT,
    title TEXT, -- Only for posts
    author TEXT,
    content_text TEXT,
    url TEXT,
    permalink TEXT,

    -- Engagement Metrics
    score INTEGER DEFAULT 0,
    upvote_ratio DECIMAL(3,2),
    num_comments INTEGER DEFAULT 0,
    gilded INTEGER DEFAULT 0,
    awards INTEGER DEFAULT 0,

    -- Content Metadata
    created_utc BIGINT,
    is_video BOOLEAN DEFAULT FALSE,
    over_18 BOOLEAN DEFAULT FALSE,
    domain TEXT,
    flair_text TEXT,

    -- AI Analysis Results
    ai_analysis JSONB DEFAULT '{}',
    relevance_score DECIMAL(3,2) DEFAULT 0,
    sentiment_score DECIMAL(3,2),
    sentiment_label TEXT DEFAULT 'neutral' CHECK (sentiment_label IN ('positive', 'negative', 'neutral')),
    confidence_score DECIMAL(3,2) DEFAULT 0,

    -- Extracted Intelligence
    key_topics TEXT[],
    mentioned_keywords TEXT[],
    extracted_entities JSONB DEFAULT '{}',
    key_insights TEXT[],
    business_context TEXT,
    actionable_intelligence TEXT,

    -- Processing Metadata
    content_metadata JSONB DEFAULT '{}',
    processing_metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Research Insights Table
-- Comprehensive insights generated from research sessions
CREATE TABLE IF NOT EXISTS public.reddit_research_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES public.reddit_research_sessions(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL,

    -- Insight Content
    insight_type TEXT DEFAULT 'comprehensive' CHECK (insight_type IN ('comprehensive', 'summary', 'trend_analysis', 'sentiment_analysis')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,

    -- Analysis Metadata
    posts_analyzed INTEGER DEFAULT 0,
    comments_analyzed INTEGER DEFAULT 0,
    avg_relevance_score DECIMAL(3,2),
    sentiment_distribution JSONB DEFAULT '{}',
    top_keywords TEXT[],
    key_findings TEXT[],
    business_opportunities TEXT[],
    actionable_recommendations TEXT[],

    -- Processing Info
    model_used TEXT DEFAULT 'gpt-5-mini',
    processing_time_seconds INTEGER,
    insight_metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_workspace_id ON public.reddit_research_sessions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_user_id ON public.reddit_research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_status ON public.reddit_research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_created_at ON public.reddit_research_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_reddit_content_session_id ON public.reddit_content(session_id);
CREATE INDEX IF NOT EXISTS idx_reddit_content_workspace_id ON public.reddit_content(workspace_id);
CREATE INDEX IF NOT EXISTS idx_reddit_content_parent_id ON public.reddit_content(parent_id);
CREATE INDEX IF NOT EXISTS idx_reddit_content_content_type ON public.reddit_content(content_type);
CREATE INDEX IF NOT EXISTS idx_reddit_content_subreddit ON public.reddit_content(subreddit);
CREATE INDEX IF NOT EXISTS idx_reddit_content_relevance_score ON public.reddit_content(relevance_score);
CREATE INDEX IF NOT EXISTS idx_reddit_content_sentiment_label ON public.reddit_content(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reddit_content_created_at ON public.reddit_content(created_at);

CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_session_id ON public.reddit_research_insights(session_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_workspace_id ON public.reddit_research_insights(workspace_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_insight_type ON public.reddit_research_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_created_at ON public.reddit_research_insights(created_at);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_reddit_content_content_text_fts ON public.reddit_content USING gin(to_tsvector('english', content_text));
CREATE INDEX IF NOT EXISTS idx_reddit_content_title_fts ON public.reddit_content USING gin(to_tsvector('english', title));

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_reddit_research_sessions_updated_at
    BEFORE UPDATE ON public.reddit_research_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reddit_content_updated_at
    BEFORE UPDATE ON public.reddit_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reddit_research_insights_updated_at
    BEFORE UPDATE ON public.reddit_research_insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Enable when ready
-- ALTER TABLE public.reddit_research_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.reddit_content ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.reddit_research_insights ENABLE ROW LEVEL SECURITY;

-- Example RLS Policies (uncomment when ready to enable)
-- CREATE POLICY "Users can access their workspace reddit sessions" ON public.reddit_research_sessions
--     FOR ALL USING (workspace_id IN (
--         SELECT id FROM public.workspaces WHERE owner_id = auth.uid()
--     ));

-- CREATE POLICY "Users can access their workspace reddit content" ON public.reddit_content
--     FOR ALL USING (workspace_id IN (
--         SELECT id FROM public.workspaces WHERE owner_id = auth.uid()
--     ));

-- CREATE POLICY "Users can access their workspace reddit insights" ON public.reddit_research_insights
--     FOR ALL USING (workspace_id IN (
--         SELECT id FROM public.workspaces WHERE owner_id = auth.uid()
--     ));
