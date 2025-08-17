import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { researchTopics, targetAudience, videoStyle } = body;

    // For now, return a mock response while we set up Chrome MCP
    const mockResponse = {
      workflowId: `workflow_${Date.now()}`,
      status: 'started',
      researchTopics: researchTopics || [],
      targetAudience: targetAudience || 'general',
      videoStyle: videoStyle || 'professional',
      message: 'Research workflow started successfully',
      nextStep: 'research_in_progress'
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
