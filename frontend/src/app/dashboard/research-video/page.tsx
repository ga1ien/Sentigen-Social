"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AlertCircle, Search, Video, Users, CheckCircle, Clock, Play, Download } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface ResearchRequest {
  topics: string[]
  platforms: string[]
  target_audience: string
  video_style: string
  max_duration: number
  research_depth: string
  content_type: string
}

interface ResearchResult {
  id: string
  status: 'researching' | 'completed' | 'failed'
  insights: any[]
  trending_topics: string[]
  engagement_data: any
  created_at: string
}

interface ScriptGeneration {
  id: string
  script: string
  quality_score: number
  target_duration: number
  status: 'generating' | 'completed' | 'approved' | 'rejected'
}

interface VideoGeneration {
  id: string
  video_url?: string
  thumbnail_url?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  avatar_id: string
  duration: number
}

export default function ResearchVideoPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [researchRequest, setResearchRequest] = useState<ResearchRequest>({
    topics: [],
    platforms: ['reddit', 'twitter', 'linkedin'],
    target_audience: '',
    video_style: 'professional',
    max_duration: 60,
    research_depth: 'comprehensive',
    content_type: 'educational'
  })
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(null)
  const [scriptGeneration, setScriptGeneration] = useState<ScriptGeneration | null>(null)
  const [videoGeneration, setVideoGeneration] = useState<VideoGeneration | null>(null)
  const [selectedAvatar, setSelectedAvatar] = useState<string>('')
  const [newTopic, setNewTopic] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const avatarOptions = [
    { id: 'professional_male', name: 'Professional Male', preview: '/avatars/professional_male.jpg' },
    { id: 'professional_female', name: 'Professional Female', preview: '/avatars/professional_female.jpg' },
    { id: 'casual_male', name: 'Casual Male', preview: '/avatars/casual_male.jpg' },
    { id: 'casual_female', name: 'Casual Female', preview: '/avatars/casual_female.jpg' }
  ]

  const addTopic = () => {
    if (newTopic.trim() && !researchRequest.topics.includes(newTopic.trim())) {
      setResearchRequest(prev => ({
        ...prev,
        topics: [...prev.topics, newTopic.trim()]
      }))
      setNewTopic('')
    }
  }

  const removeTopic = (topic: string) => {
    setResearchRequest(prev => ({
      ...prev,
      topics: prev.topics.filter(t => t !== topic)
    }))
  }

  const startResearch = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/research-video/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          research_topics: researchRequest.topics,
          platforms_to_research: researchRequest.platforms,
          target_audience: researchRequest.target_audience,
          video_style: researchRequest.video_style,
          max_video_duration: researchRequest.max_duration
        })
      })

      const result = await response.json()
      if (result.workflow_id) {
        setCurrentStep(2)
        // Start polling for research results
        pollResearchStatus(result.workflow_id)
      }
    } catch (error) {
      console.error('Failed to start research:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const pollResearchStatus = async (workflowId: string) => {
    // Poll every 5 seconds for research completion
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/research-video/status/${workflowId}`)
        const status = await response.json()

        if (status.status === 'research_completed') {
          setResearchResult(status.research_data)
          setCurrentStep(3)
          clearInterval(interval)
        } else if (status.status === 'failed') {
          clearInterval(interval)
          // Handle error
        }
      } catch (error) {
        console.error('Failed to poll status:', error)
      }
    }, 5000)
  }

  const generateScript = async () => {
    if (!researchResult) return

    setIsLoading(true)
    try {
      const response = await fetch('/api/research-video/generate-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          research_data: researchResult,
          target_audience: researchRequest.target_audience,
          video_style: researchRequest.video_style,
          max_duration: researchRequest.max_duration
        })
      })

      const result = await response.json()
      setScriptGeneration(result)
      setCurrentStep(4)
    } catch (error) {
      console.error('Failed to generate script:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const approveScript = async () => {
    if (!scriptGeneration) return

    setScriptGeneration(prev => prev ? { ...prev, status: 'approved' } : null)
    setCurrentStep(5)
  }

  const generateVideo = async () => {
    if (!scriptGeneration || !selectedAvatar) return

    setIsLoading(true)
    try {
      const response = await fetch('/api/research-video/generate-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_id: scriptGeneration.id,
          avatar_id: selectedAvatar,
          video_style: researchRequest.video_style
        })
      })

      const result = await response.json()
      setVideoGeneration(result)
      setCurrentStep(6)
    } catch (error) {
      console.error('Failed to generate video:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const publishVideo = async () => {
    if (!videoGeneration) return

    setIsLoading(true)
    try {
      const response = await fetch('/api/research-video/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: videoGeneration.id,
          platforms: ['tiktok', 'instagram_reels', 'youtube_shorts'],
          hashtags: researchResult?.trending_topics || []
        })
      })

      const result = await response.json()
      setCurrentStep(7)
    } catch (error) {
      console.error('Failed to publish video:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStepProgress = () => {
    return (currentStep / 7) * 100
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Research-to-Video Workflow</h1>
        <p className="text-muted-foreground">
          Automatically research trending topics, generate scripts, create AI videos, and publish to social platforms
        </p>

        <div className="mt-6">
          <div className="flex justify-between text-sm text-muted-foreground mb-2">
            <span>Progress</span>
            <span>{currentStep}/7 steps</span>
          </div>
          <Progress value={getStepProgress()} className="h-2" />
        </div>
      </div>

      <Tabs value={currentStep.toString()} className="space-y-6">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="1" className="text-xs">Research Setup</TabsTrigger>
          <TabsTrigger value="2" className="text-xs">Researching</TabsTrigger>
          <TabsTrigger value="3" className="text-xs">Review Data</TabsTrigger>
          <TabsTrigger value="4" className="text-xs">Script Review</TabsTrigger>
          <TabsTrigger value="5" className="text-xs">Avatar Selection</TabsTrigger>
          <TabsTrigger value="6" className="text-xs">Video Approval</TabsTrigger>
          <TabsTrigger value="7" className="text-xs">Publishing</TabsTrigger>
        </TabsList>

        {/* Step 1: Research Setup */}
        <TabsContent value="1" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Research Configuration
              </CardTitle>
              <CardDescription>
                Define what topics to research and how to analyze the data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <Label htmlFor="topics">Research Topics</Label>
                <div className="flex gap-2">
                  <Input
                    id="topics"
                    placeholder="Enter a topic (e.g., AI automation, productivity tools)"
                    value={newTopic}
                    onChange={(e) => setNewTopic(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addTopic()}
                  />
                  <Button onClick={addTopic} variant="outline">Add</Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {researchRequest.topics.map((topic) => (
                    <Badge key={topic} variant="secondary" className="cursor-pointer"
                           onClick={() => removeTopic(topic)}>
                      {topic} ×
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="target_audience">Target Audience</Label>
                  <Input
                    id="target_audience"
                    placeholder="e.g., tech entrepreneurs, developers"
                    value={researchRequest.target_audience}
                    onChange={(e) => setResearchRequest(prev => ({ ...prev, target_audience: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="video_style">Video Style</Label>
                  <Select value={researchRequest.video_style}
                          onValueChange={(value) => setResearchRequest(prev => ({ ...prev, video_style: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="casual">Casual</SelectItem>
                      <SelectItem value="educational">Educational</SelectItem>
                      <SelectItem value="entertaining">Entertaining</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max_duration">Max Video Duration (seconds)</Label>
                  <Input
                    id="max_duration"
                    type="number"
                    min="15"
                    max="180"
                    value={researchRequest.max_duration}
                    onChange={(e) => setResearchRequest(prev => ({ ...prev, max_duration: parseInt(e.target.value) }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="research_depth">Research Depth</Label>
                  <Select value={researchRequest.research_depth}
                          onValueChange={(value) => setResearchRequest(prev => ({ ...prev, research_depth: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quick">Quick (5-10 sources)</SelectItem>
                      <SelectItem value="comprehensive">Comprehensive (15-25 sources)</SelectItem>
                      <SelectItem value="deep">Deep (30+ sources)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button
                onClick={startResearch}
                disabled={researchRequest.topics.length === 0 || !researchRequest.target_audience || isLoading}
                className="w-full"
              >
                {isLoading ? 'Starting Research...' : 'Start Research'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Step 2: Researching */}
        <TabsContent value="2" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 animate-spin" />
                Research in Progress
              </CardTitle>
              <CardDescription>
                AI is researching your topics across multiple platforms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Scanning Reddit discussions...</span>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                </div>
                <div className="flex items-center justify-between">
                  <span>Analyzing Twitter trends...</span>
                  <Clock className="h-5 w-5 animate-spin text-blue-500" />
                </div>
                <div className="flex items-center justify-between">
                  <span>Gathering LinkedIn insights...</span>
                  <Clock className="h-5 w-5 animate-spin text-blue-500" />
                </div>
                <div className="flex items-center justify-between">
                  <span>Processing engagement data...</span>
                  <Clock className="h-5 w-5 animate-spin text-blue-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Step 3: Review Research Data */}
        <TabsContent value="3" className="space-y-6">
          {researchResult && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  Research Complete
                </CardTitle>
                <CardDescription>
                  Review the research findings and generate a script
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Trending Topics Found:</h4>
                  <div className="flex flex-wrap gap-2">
                    {researchResult.trending_topics.map((topic) => (
                      <Badge key={topic} variant="outline">{topic}</Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Key Insights:</h4>
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="text-sm">
                      Found {researchResult.insights.length} relevant discussions with high engagement.
                      Average engagement rate: {researchResult.engagement_data?.average_engagement || 'N/A'}%
                    </p>
                  </div>
                </div>

                <Button onClick={generateScript} disabled={isLoading} className="w-full">
                  {isLoading ? 'Generating Script...' : 'Generate Script from Research'}
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Step 4: Script Review */}
        <TabsContent value="4" className="space-y-6">
          {scriptGeneration && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Video className="h-5 w-5" />
                  Generated Script
                </CardTitle>
                <CardDescription>
                  Review and approve the AI-generated script
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-muted p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium">Quality Score: {scriptGeneration.quality_score}/10</span>
                    <span className="text-sm text-muted-foreground">
                      Est. Duration: {scriptGeneration.target_duration}s
                    </span>
                  </div>
                  <Textarea
                    value={scriptGeneration.script}
                    onChange={(e) => setScriptGeneration(prev =>
                      prev ? { ...prev, script: e.target.value } : null
                    )}
                    rows={10}
                    className="font-mono text-sm"
                  />
                </div>

                <div className="flex gap-2">
                  <Button onClick={approveScript} className="flex-1">
                    Approve Script
                  </Button>
                  <Button variant="outline" onClick={generateScript} disabled={isLoading}>
                    Regenerate
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Step 5: Avatar Selection */}
        <TabsContent value="5" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Choose Avatar
              </CardTitle>
              <CardDescription>
                Select an AI avatar to present your video
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {avatarOptions.map((avatar) => (
                  <div
                    key={avatar.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedAvatar === avatar.id ? 'border-primary bg-primary/5' : 'border-muted'
                    }`}
                    onClick={() => setSelectedAvatar(avatar.id)}
                  >
                    <div className="aspect-square bg-muted rounded-lg mb-2"></div>
                    <h4 className="font-medium text-sm">{avatar.name}</h4>
                  </div>
                ))}
              </div>

              <Button
                onClick={generateVideo}
                disabled={!selectedAvatar || isLoading}
                className="w-full mt-4"
              >
                {isLoading ? 'Generating Video...' : 'Generate Video'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Step 6: Video Approval */}
        <TabsContent value="6" className="space-y-6">
          {videoGeneration && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Play className="h-5 w-5" />
                  Video Preview
                </CardTitle>
                <CardDescription>
                  Review the generated video before publishing
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {videoGeneration.status === 'completed' && videoGeneration.video_url ? (
                  <div className="space-y-4">
                    <div className="aspect-video bg-black rounded-lg flex items-center justify-center">
                      <video
                        src={videoGeneration.video_url}
                        controls
                        className="w-full h-full rounded-lg"
                      />
                    </div>

                    <div className="flex gap-2">
                      <Button onClick={publishVideo} className="flex-1">
                        Approve & Publish
                      </Button>
                      <Button variant="outline" onClick={() => setCurrentStep(5)}>
                        Regenerate
                      </Button>
                      <Button variant="outline">
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Clock className="h-8 w-8 animate-spin mx-auto mb-2" />
                    <p>Video is being generated...</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Step 7: Publishing */}
        <TabsContent value="7" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Publishing Complete
              </CardTitle>
              <CardDescription>
                Your video has been published to all selected platforms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    Video successfully published to TikTok, Instagram Reels, and YouTube Shorts!
                  </AlertDescription>
                </Alert>

                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <h4 className="font-medium">TikTok</h4>
                    <p className="text-sm text-muted-foreground">Published</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <h4 className="font-medium">Instagram Reels</h4>
                    <p className="text-sm text-muted-foreground">Published</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <h4 className="font-medium">YouTube Shorts</h4>
                    <p className="text-sm text-muted-foreground">Published</p>
                  </div>
                </div>

                <Button onClick={() => setCurrentStep(1)} variant="outline" className="w-full">
                  Start New Research Project
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
