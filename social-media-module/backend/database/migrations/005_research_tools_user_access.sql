-- =====================================================
-- Research Tools User Access Migration
-- Enables proper user access control for all research tools
-- =====================================================

-- Enable Row Level Security on all research tables
ALTER TABLE public.reddit_research_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reddit_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reddit_research_insights ENABLE ROW LEVEL SECURITY;

-- Reddit Research Policies
CREATE POLICY "Users can access their workspace reddit sessions" ON public.reddit_research_sessions
    FOR ALL USING (
        workspace_id IN (
            SELECT w.id FROM public.workspaces w
            WHERE w.owner_id = auth.uid()
            UNION
            SELECT wm.workspace_id FROM public.workspace_members wm
            WHERE wm.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can access their workspace reddit content" ON public.reddit_content
    FOR ALL USING (
        workspace_id IN (
            SELECT w.id FROM public.workspaces w
            WHERE w.owner_id = auth.uid()
            UNION
            SELECT wm.workspace_id FROM public.workspace_members wm
            WHERE wm.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can access their workspace reddit insights" ON public.reddit_research_insights
    FOR ALL USING (
        workspace_id IN (
            SELECT w.id FROM public.workspaces w
            WHERE w.owner_id = auth.uid()
            UNION
            SELECT wm.workspace_id FROM public.workspace_members wm
            WHERE wm.user_id = auth.uid()
        )
    );

-- Create research configurations table for all sources
CREATE TABLE IF NOT EXISTS public.research_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
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

-- Enable RLS on research configurations
ALTER TABLE public.research_configurations ENABLE ROW LEVEL SECURITY;

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

-- Create research jobs table for tracking execution
CREATE TABLE IF NOT EXISTS public.research_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
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

-- Enable RLS on research jobs
ALTER TABLE public.research_jobs ENABLE ROW LEVEL SECURITY;

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

-- Create research results table for storing analysis outputs
CREATE TABLE IF NOT EXISTS public.research_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES public.research_jobs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
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

-- Enable RLS on research results
ALTER TABLE public.research_results ENABLE ROW LEVEL SECURITY;

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

-- Create functions for common operations
CREATE OR REPLACE FUNCTION public.get_user_research_stats(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_configurations', COUNT(DISTINCT rc.id),
        'active_configurations', COUNT(DISTINCT rc.id) FILTER (WHERE rc.is_active = TRUE),
        'total_jobs', COUNT(DISTINCT rj.id),
        'completed_jobs', COUNT(DISTINCT rj.id) FILTER (WHERE rj.status = 'completed'),
        'failed_jobs', COUNT(DISTINCT rj.id) FILTER (WHERE rj.status = 'failed'),
        'total_results', COUNT(DISTINCT rr.id),
        'sources_used', array_agg(DISTINCT rc.source_type),
        'last_activity', MAX(GREATEST(rc.updated_at, rj.updated_at, rr.updated_at))
    ) INTO result
    FROM public.research_configurations rc
    LEFT JOIN public.research_jobs rj ON rc.id = rj.configuration_id
    LEFT JOIN public.research_results rr ON rj.id = rr.job_id
    WHERE rc.user_id = p_user_id;

    RETURN COALESCE(result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check user permissions
CREATE OR REPLACE FUNCTION public.check_research_permissions(p_user_id UUID, p_workspace_id UUID)
RETURNS JSONB AS $$
DECLARE
    user_record RECORD;
    workspace_role TEXT;
    permissions JSONB;
BEGIN
    -- Get user details
    SELECT * INTO user_record FROM public.users WHERE id = p_user_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'User not found');
    END IF;

    -- Check workspace access
    SELECT role INTO workspace_role
    FROM public.workspace_members
    WHERE user_id = p_user_id AND workspace_id = p_workspace_id;

    IF NOT FOUND THEN
        -- Check if user owns the workspace
        SELECT 'owner' INTO workspace_role
        FROM public.workspaces
        WHERE id = p_workspace_id AND owner_id = p_user_id;

        IF NOT FOUND THEN
            RETURN jsonb_build_object('error', 'No access to workspace');
        END IF;
    END IF;

    -- Calculate permissions based on subscription tier
    permissions := jsonb_build_object(
        'can_create_research', TRUE,
        'can_schedule_research', TRUE,
        'can_access_ai_analysis', TRUE,
        'workspace_role', workspace_role,
        'subscription_tier', user_record.subscription_tier,
        'is_admin', user_record.is_admin
    );

    -- Adjust limits based on subscription
    CASE user_record.subscription_tier
        WHEN 'free' THEN
            permissions := permissions || jsonb_build_object(
                'max_concurrent_jobs', 1,
                'max_configurations', 5,
                'sources_available', ARRAY['reddit', 'hackernews', 'github']
            );
        WHEN 'starter' THEN
            permissions := permissions || jsonb_build_object(
                'max_concurrent_jobs', 3,
                'max_configurations', 15,
                'sources_available', ARRAY['reddit', 'hackernews', 'github']
            );
        WHEN 'creator' THEN
            permissions := permissions || jsonb_build_object(
                'max_concurrent_jobs', 5,
                'max_configurations', 50,
                'sources_available', ARRAY['reddit', 'hackernews', 'github', 'linkedin']
            );
        WHEN 'creator_pro' THEN
            permissions := permissions || jsonb_build_object(
                'max_concurrent_jobs', 10,
                'max_configurations', 100,
                'sources_available', ARRAY['reddit', 'hackernews', 'github', 'linkedin', 'twitter']
            );
        WHEN 'enterprise' THEN
            permissions := permissions || jsonb_build_object(
                'max_concurrent_jobs', 50,
                'max_configurations', 500,
                'sources_available', ARRAY['reddit', 'hackernews', 'github', 'linkedin', 'twitter']
            );
        ELSE
            permissions := permissions || jsonb_build_object(
                'max_concurrent_jobs', 1,
                'max_configurations', 5,
                'sources_available', ARRAY['reddit', 'hackernews', 'github']
            );
    END CASE;

    -- Admin overrides
    IF user_record.is_admin THEN
        permissions := permissions || jsonb_build_object(
            'max_concurrent_jobs', 100,
            'max_configurations', 1000,
            'can_access_all_workspaces', TRUE,
            'can_manage_users', TRUE
        );
    END IF;

    RETURN permissions;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at triggers
CREATE TRIGGER update_research_configurations_updated_at
    BEFORE UPDATE ON public.research_configurations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_research_jobs_updated_at
    BEFORE UPDATE ON public.research_jobs
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_research_results_updated_at
    BEFORE UPDATE ON public.research_results
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON public.research_configurations TO authenticated;
GRANT ALL ON public.research_jobs TO authenticated;
GRANT ALL ON public.research_results TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_user_research_stats TO authenticated;
GRANT EXECUTE ON FUNCTION public.check_research_permissions TO authenticated;
