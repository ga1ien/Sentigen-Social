import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const workflowId = id;

    // Mock status response - will be replaced with real Chrome MCP integration
    const mockStatus = {
      workflow_id: workflowId,
      status: 'research_complete',
      progress: 85,
      current_step: 'script_generation',
      research_data: {
        sources_found: 12,
        insights_extracted: 8,
        trending_topics: ['AI automation', 'productivity tools', 'remote work'],
        sentiment_analysis: 'positive'
      },
      script_preview: 'AI is revolutionizing how we work...',
      next_actions: ['review_script', 'select_avatar', 'generate_video']
    };

    return NextResponse.json(mockStatus);
  } catch (error) {
    console.error('Error getting workflow status:', error);
    return NextResponse.json(
      { error: 'Failed to get workflow status' },
      { status: 500 }
    );
  }
}
