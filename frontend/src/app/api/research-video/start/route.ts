import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { research_topics, target_audience, video_style } = body;

    // For now, return a mock response while we set up Chrome MCP
    const mockResponse = {
      workflow_id: `workflow_${Date.now()}`,
      status: 'started',
      research_topics: research_topics || [],
      target_audience: target_audience || 'general',
      video_style: video_style || 'professional',
      message: 'Research workflow started successfully',
      next_step: 'research_in_progress'
    };

    return NextResponse.json(mockResponse);
  } catch (error) {
    console.error('Error starting research workflow:', error);
    return NextResponse.json(
      { error: 'Failed to start research workflow' },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({ message: 'Research Video API is running' });
}
