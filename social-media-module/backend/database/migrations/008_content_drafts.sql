-- Content Drafts table for saving user drafts
CREATE TABLE IF NOT EXISTS public.content_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    platform TEXT,
    title TEXT,
    content TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_content_drafts_user_id ON public.content_drafts(user_id);
CREATE INDEX IF NOT EXISTS idx_content_drafts_status ON public.content_drafts(status);
CREATE INDEX IF NOT EXISTS idx_content_drafts_created_at ON public.content_drafts(created_at DESC);
