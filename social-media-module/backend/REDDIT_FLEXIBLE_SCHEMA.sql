-- Flexible Reddit Research Schema for Supabase
-- Works with any research topics, not just AI automation tools
-- Consolidated into fewer tables with more columns

-- Main Reddit research sessions table
CREATE TABLE IF NOT EXISTS public.reddit_research_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    session_name TEXT NOT NULL,
    search_query TEXT NOT NULL,
    research_topic TEXT, -- General topic like "AI tools", "Marketing strategies", etc.
    target_keywords TEXT[] DEFAULT '{}', -- Keywords to track mentions of
    target_subreddits TEXT[] DEFAULT '{}', -- Subreddits searched
    search_parameters JSONB DEFAULT '{}', -- time_filter, sort_by, limits, etc.
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress FLOAT DEFAULT 0.0 CHECK (progress >= 0 AND progress <= 1),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_posts_found INTEGER DEFAULT 0,
    total_comments_found INTEGER DEFAULT 0,
    posts_analyzed INTEGER DEFAULT 0,
    comments_analyzed INTEGER DEFAULT 0,
    ai_analysis_prompt TEXT,
    session_metadata JSONB DEFAULT '{}',
    session_stats JSONB DEFAULT '{}', -- Aggregated statistics
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Consolidated Reddit content table (posts + comments)
CREATE TABLE IF NOT EXISTS public.reddit_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.reddit_research_sessions(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,

    -- Reddit identifiers
    reddit_id TEXT NOT NULL, -- Reddit's internal ID (post or comment)
    content_type TEXT NOT NULL CHECK (content_type IN ('post', 'comment')),
    parent_id UUID REFERENCES public.reddit_content(id) ON DELETE CASCADE, -- For comments, references the post

    -- Content data
    subreddit TEXT NOT NULL,
    title TEXT, -- Only for posts
    author TEXT,
    content_text TEXT NOT NULL, -- selftext for posts, body for comments
    url TEXT, -- Only for posts
    permalink TEXT,

    -- Engagement metrics
    score INTEGER DEFAULT 0,
    upvote_ratio FLOAT, -- Only for posts
    num_comments INTEGER DEFAULT 0, -- Only for posts
    created_utc BIGINT,

    -- Content metadata
    is_video BOOLEAN DEFAULT FALSE,
    domain TEXT, -- Only for posts
    flair_text TEXT,
    gilded INTEGER DEFAULT 0,
    awards INTEGER DEFAULT 0,
    over_18 BOOLEAN DEFAULT FALSE,

    -- AI Analysis results
    ai_analysis JSONB DEFAULT '{}', -- Full AI analysis response
    relevance_score FLOAT DEFAULT 0, -- How relevant to the research topic (0-1)
    sentiment_score FLOAT, -- Sentiment analysis (-1 to 1)
    sentiment_label TEXT, -- 'positive', 'negative', 'neutral'
    confidence_score FLOAT DEFAULT 0, -- AI confidence in analysis (0-1)

    -- Extracted insights
    key_topics TEXT[] DEFAULT '{}', -- AI-extracted topics
    mentioned_keywords TEXT[] DEFAULT '{}', -- Keywords found in content
    extracted_entities JSONB DEFAULT '{}', -- Named entities, brands, tools, etc.
    key_insights TEXT[] DEFAULT '{}', -- Main takeaways from AI analysis
    business_context TEXT, -- Business use case or context identified
    actionable_intelligence TEXT, -- What can be learned from this content

    -- Content metadata
    content_metadata JSONB DEFAULT '{}', -- Original Reddit data
    processing_metadata JSONB DEFAULT '{}', -- Processing timestamps, model used, etc.

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(reddit_id, session_id)
);

-- Research insights and summaries table
CREATE TABLE IF NOT EXISTS public.reddit_research_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.reddit_research_sessions(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,

    -- Insight metadata
    insight_type TEXT NOT NULL, -- 'trend_analysis', 'sentiment_summary', 'keyword_analysis', 'comprehensive_report', etc.
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    detailed_analysis TEXT, -- Full AI-generated analysis

    -- Structured insights
    key_findings TEXT[] DEFAULT '{}',
    trending_topics TEXT[] DEFAULT '{}',
    top_keywords TEXT[] DEFAULT '{}',
    sentiment_distribution JSONB DEFAULT '{}', -- Positive/negative/neutral counts
    engagement_patterns JSONB DEFAULT '{}', -- Score distributions, timing patterns, etc.
    subreddit_breakdown JSONB DEFAULT '{}', -- Performance by subreddit
    recommended_actions TEXT[] DEFAULT '{}',

    -- Analysis metadata
    confidence_score FLOAT DEFAULT 0,
    data_sources JSONB DEFAULT '{}', -- References to content used
    content_sample_size INTEGER DEFAULT 0, -- How many posts/comments analyzed
    generated_by TEXT DEFAULT 'gpt-5-mini', -- AI model used
    generation_parameters JSONB DEFAULT '{}', -- Model parameters used

    -- Validation and quality
    is_validated BOOLEAN DEFAULT FALSE,
    validation_notes TEXT,
    quality_score FLOAT, -- Internal quality assessment

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create comprehensive indexes for performance
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_workspace_id ON public.reddit_research_sessions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_user_id ON public.reddit_research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_status ON public.reddit_research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_topic ON public.reddit_research_sessions(research_topic);
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_created_at ON public.reddit_research_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reddit_research_sessions_keywords ON public.reddit_research_sessions USING GIN (target_keywords);

CREATE INDEX IF NOT EXISTS idx_reddit_content_session_id ON public.reddit_content(session_id);
CREATE INDEX IF NOT EXISTS idx_reddit_content_workspace_id ON public.reddit_content(workspace_id);
CREATE INDEX IF NOT EXISTS idx_reddit_content_type ON public.reddit_content(content_type);
CREATE INDEX IF NOT EXISTS idx_reddit_content_parent_id ON public.reddit_content(parent_id);
CREATE INDEX IF NOT EXISTS idx_reddit_content_subreddit ON public.reddit_content(subreddit);
CREATE INDEX IF NOT EXISTS idx_reddit_content_score ON public.reddit_content(score DESC);
CREATE INDEX IF NOT EXISTS idx_reddit_content_relevance_score ON public.reddit_content(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_reddit_content_sentiment ON public.reddit_content(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reddit_content_created_utc ON public.reddit_content(created_utc DESC);
CREATE INDEX IF NOT EXISTS idx_reddit_content_key_topics ON public.reddit_content USING GIN (key_topics);
CREATE INDEX IF NOT EXISTS idx_reddit_content_mentioned_keywords ON public.reddit_content USING GIN (mentioned_keywords);
CREATE INDEX IF NOT EXISTS idx_reddit_content_extracted_entities ON public.reddit_content USING GIN (extracted_entities);

CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_session_id ON public.reddit_research_insights(session_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_workspace_id ON public.reddit_research_insights(workspace_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_user_id ON public.reddit_research_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_type ON public.reddit_research_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_reddit_research_insights_created_at ON public.reddit_research_insights(created_at DESC);

-- Create trigger function for updated_at columns
CREATE OR REPLACE FUNCTION update_reddit_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_reddit_research_sessions_updated_at') THEN
        CREATE TRIGGER update_reddit_research_sessions_updated_at
        BEFORE UPDATE ON public.reddit_research_sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_reddit_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_reddit_content_updated_at') THEN
        CREATE TRIGGER update_reddit_content_updated_at
        BEFORE UPDATE ON public.reddit_content
        FOR EACH ROW
        EXECUTE FUNCTION update_reddit_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_reddit_research_insights_updated_at') THEN
        CREATE TRIGGER update_reddit_research_insights_updated_at
        BEFORE UPDATE ON public.reddit_research_insights
        FOR EACH ROW
        EXECUTE FUNCTION update_reddit_updated_at_column();
    END IF;
END
$$;

-- Utility functions for analytics

-- Function to get comprehensive session statistics
CREATE OR REPLACE FUNCTION get_reddit_session_stats(p_session_id UUID)
RETURNS TABLE (
    total_posts bigint,
    total_comments bigint,
    unique_subreddits bigint,
    avg_post_score numeric,
    avg_relevance_score numeric,
    sentiment_distribution jsonb,
    top_keywords text[],
    top_subreddits jsonb,
    engagement_summary jsonb
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) FILTER (WHERE content_type = 'post') as total_posts,
        COUNT(*) FILTER (WHERE content_type = 'comment') as total_comments,
        COUNT(DISTINCT subreddit) as unique_subreddits,
        AVG(score) FILTER (WHERE content_type = 'post') as avg_post_score,
        AVG(relevance_score) as avg_relevance_score,
        jsonb_build_object(
            'positive', COUNT(*) FILTER (WHERE sentiment_label = 'positive'),
            'negative', COUNT(*) FILTER (WHERE sentiment_label = 'negative'),
            'neutral', COUNT(*) FILTER (WHERE sentiment_label = 'neutral')
        ) as sentiment_distribution,
        ARRAY_AGG(DISTINCT unnest(mentioned_keywords)) FILTER (WHERE array_length(mentioned_keywords, 1) > 0) as top_keywords,
        jsonb_object_agg(
            subreddit,
            jsonb_build_object(
                'posts', COUNT(*) FILTER (WHERE content_type = 'post'),
                'avg_score', AVG(score),
                'avg_relevance', AVG(relevance_score)
            )
        ) as top_subreddits,
        jsonb_build_object(
            'total_score', SUM(score),
            'high_relevance_content', COUNT(*) FILTER (WHERE relevance_score > 0.7),
            'highly_engaged_content', COUNT(*) FILTER (WHERE score > 100)
        ) as engagement_summary
    FROM public.reddit_content
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Function to extract and analyze keyword mentions
CREATE OR REPLACE FUNCTION analyze_keyword_mentions(p_session_id UUID, p_keywords text[])
RETURNS TABLE (
    keyword TEXT,
    mention_count bigint,
    avg_sentiment_score numeric,
    avg_relevance_score numeric,
    top_contexts text[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        keyword_item as keyword,
        COUNT(*) as mention_count,
        AVG(sentiment_score) as avg_sentiment_score,
        AVG(relevance_score) as avg_relevance_score,
        ARRAY_AGG(DISTINCT SUBSTRING(content_text FROM 1 FOR 100)) as top_contexts
    FROM public.reddit_content,
         unnest(p_keywords) as keyword_item
    WHERE session_id = p_session_id
      AND (
          LOWER(content_text) LIKE '%' || LOWER(keyword_item) || '%' OR
          LOWER(title) LIKE '%' || LOWER(keyword_item) || '%' OR
          keyword_item = ANY(mentioned_keywords)
      )
    GROUP BY keyword_item
    ORDER BY mention_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get trending topics across sessions
CREATE OR REPLACE FUNCTION get_trending_topics(p_workspace_id UUID, p_days INTEGER DEFAULT 7)
RETURNS TABLE (
    topic TEXT,
    mention_count bigint,
    avg_sentiment numeric,
    recent_sessions bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        topic_item as topic,
        COUNT(*) as mention_count,
        AVG(sentiment_score) as avg_sentiment,
        COUNT(DISTINCT rc.session_id) as recent_sessions
    FROM public.reddit_content rc
    JOIN public.reddit_research_sessions rrs ON rc.session_id = rrs.id,
         unnest(rc.key_topics) as topic_item
    WHERE rc.workspace_id = p_workspace_id
      AND rc.created_at > NOW() - INTERVAL '1 day' * p_days
    GROUP BY topic_item
    HAVING COUNT(*) > 1
    ORDER BY mention_count DESC, avg_sentiment DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Row Level Security policies
ALTER TABLE public.reddit_research_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reddit_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reddit_research_insights ENABLE ROW LEVEL SECURITY;

-- Users can access Reddit data in their workspaces
CREATE POLICY "Users can view Reddit sessions in their workspaces" ON public.reddit_research_sessions FOR SELECT
USING (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can create Reddit sessions in their workspaces" ON public.reddit_research_sessions FOR INSERT
WITH CHECK (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can update Reddit sessions in their workspaces" ON public.reddit_research_sessions FOR UPDATE
USING (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can view Reddit content in their workspaces" ON public.reddit_content FOR SELECT
USING (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can create Reddit content in their workspaces" ON public.reddit_content FOR INSERT
WITH CHECK (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can update Reddit content in their workspaces" ON public.reddit_content FOR UPDATE
USING (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can view Reddit insights in their workspaces" ON public.reddit_research_insights FOR SELECT
USING (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can create Reddit insights in their workspaces" ON public.reddit_research_insights FOR INSERT
WITH CHECK (
    workspace_id IN (
        SELECT workspace_id FROM public.workspace_members
        WHERE user_id = auth.uid()
    )
);

-- Table comments for documentation
COMMENT ON TABLE public.reddit_research_sessions IS 'Flexible Reddit research sessions for any topic with AI analysis parameters';
COMMENT ON TABLE public.reddit_content IS 'Consolidated Reddit posts and comments with comprehensive AI analysis';
COMMENT ON TABLE public.reddit_research_insights IS 'AI-generated insights and summaries from Reddit research sessions';

COMMENT ON COLUMN public.reddit_research_sessions.research_topic IS 'General research topic like "AI tools", "Marketing strategies", "Crypto trends", etc.';
COMMENT ON COLUMN public.reddit_research_sessions.target_keywords IS 'Keywords to track mentions of (flexible for any domain)';
COMMENT ON COLUMN public.reddit_content.content_type IS 'Either "post" or "comment" - consolidated table for both';
COMMENT ON COLUMN public.reddit_content.extracted_entities IS 'Named entities like brands, tools, people, companies extracted by AI';
COMMENT ON COLUMN public.reddit_content.mentioned_keywords IS 'Keywords from target list found in this content';

-- Schema complete for flexible Reddit research
