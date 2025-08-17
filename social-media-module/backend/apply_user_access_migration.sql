-- Apply this SQL directly in Supabase SQL Editor
-- User Access System Migration for Research Tools

-- Enable Row Level Security on existing research tables
ALTER TABLE public.reddit_research_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reddit_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reddit_research_insights ENABLE ROW LEVEL SECURITY;

-- Create research configurations table for all sources
CREATE TABLE IF NOT EXISTS public.research_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK (source_type IN ('reddit', 'hackernews', 'github', 'linkedin', 'twitter')),
    config_name TEXT NOT NULL,
    description TEXT,
    configuration JSONB NOT NULL DEFAULT '{}',
    schedule JSONB DEFAULT '{}',
    auto_run_enabled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_run_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, workspace_id, source_type, config_name)
);

-- Create research jobs table for tracking execution
CREATE TABLE IF NOT EXISTS public.research_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    configuration_id UUID REFERENCES public.research_configurations(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK (source_type IN ('reddit', 'hackernews', 'github', 'linkedin', 'twitter')),
    job_type TEXT NOT NULL CHECK (job_type IN ('raw', 'analyze', 'pipeline')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    results_path TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create research results table for storing analysis outputs
CREATE TABLE IF NOT EXISTS public.research_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES public.research_jobs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK (source_type IN ('reddit', 'hackernews', 'github', 'linkedin', 'twitter')),
    result_type TEXT NOT NULL CHECK (result_type IN ('raw_data', 'analyzed_data', 'insights', 'summary')),
    title TEXT,
    content JSONB NOT NULL DEFAULT '{}',
    summary TEXT,
    insights JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on new tables
ALTER TABLE public.research_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_results ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can manage their research configurations" ON public.research_configurations
    FOR ALL USING (
        user_id = auth.uid() OR
        workspace_id IN (
            SELECT w.id FROM public.workspaces w
            WHERE w.owner_id = auth.uid()
            UNION
            SELECT wm.workspace_id FROM public.workspace_members wm
            WHERE wm.user_id = auth.uid() AND wm.role IN ('owner', 'admin', 'editor')
        )
    );

CREATE POLICY "Users can access their research jobs" ON public.research_jobs
    FOR ALL USING (
        user_id = auth.uid() OR
        workspace_id IN (
            SELECT w.id FROM public.workspaces w
            WHERE w.owner_id = auth.uid()
            UNION
            SELECT wm.workspace_id FROM public.workspace_members wm
            WHERE wm.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can access their research results" ON public.research_results
    FOR ALL USING (
        user_id = auth.uid() OR
        is_public = TRUE OR
        workspace_id IN (
            SELECT w.id FROM public.workspaces w
            WHERE w.owner_id = auth.uid()
            UNION
            SELECT wm.workspace_id FROM public.workspace_members wm
            WHERE wm.user_id = auth.uid()
        )
    );

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_research_configurations_user_workspace ON public.research_configurations(user_id, workspace_id);
CREATE INDEX IF NOT EXISTS idx_research_configurations_source ON public.research_configurations(source_type);
CREATE INDEX IF NOT EXISTS idx_research_jobs_user_workspace ON public.research_jobs(user_id, workspace_id);
CREATE INDEX IF NOT EXISTS idx_research_jobs_status ON public.research_jobs(status);
CREATE INDEX IF NOT EXISTS idx_research_jobs_created_at ON public.research_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_research_results_user_workspace ON public.research_results(user_id, workspace_id);
CREATE INDEX IF NOT EXISTS idx_research_results_source ON public.research_results(source_type);
CREATE INDEX IF NOT EXISTS idx_research_results_public ON public.research_results(is_public) WHERE is_public = TRUE;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON public.research_configurations TO authenticated;
GRANT ALL ON public.research_jobs TO authenticated;
GRANT ALL ON public.research_results TO authenticated;
