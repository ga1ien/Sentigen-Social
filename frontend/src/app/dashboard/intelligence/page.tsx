"use client"

import { useState, useEffect } from 'react'
import { useUser } from '@/contexts/user-context'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { toast } from '@/lib/toast-filter'
import api from '@/lib/api'
import {
  Search,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  Eye,
  Trash2,
  RefreshCw,
  BarChart3,
  TrendingUp,
  Users,
  MessageSquare,
  Star,
  GitBranch,
  Github,
  Zap,
  Plus,
  Globe,
  Hash
} from 'lucide-react'

interface ResearchSession {
  id: string
  source: string
  query: string
  status: string
  results_count: number
  created_at: string
  completed_at?: string
}

interface ResearchResult {
  id: string
  status: string
  source: string
  query: string
  results_count: number
  insights: any
  raw_data: any[]
  created_at: string
  completed_at?: string
}

const sourceIcons = {
  reddit: Hash, // Using Hash icon instead of Reddit
  hackernews: Zap,
  github: Github,
  google_trends: Globe
}

const sourceColors = {
  reddit: '#FF4500',
  hackernews: '#FF6600',
  github: '#333333',
  google_trends: '#4285F4'
}

export default function ContentIntelligencePage() {
  const { user, loading } = useUser()
  // Using filtered toast that only shows warnings/errors
  const [sessions, setSessions] = useState<ResearchSession[]>([])
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [selectedResult, setSelectedResult] = useState<ResearchResult | null>(null)
  const [isResultDialogOpen, setIsResultDialogOpen] = useState(false)
  const [isGeneratingContent, setIsGeneratingContent] = useState(false)
  const [generatedContent, setGeneratedContent] = useState<any>(null)

  // New research form state
  const [newResearch, setNewResearch] = useState({
    query: '',
    source: 'reddit',
    max_items: 10,
    analysis_depth: 'standard'
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (user && !loading) {
      loadResearchSessions()
    }
  }, [user, loading])

  const loadResearchSessions = async () => {
    try {
      setLoadingSessions(true)
      const response = await api.get('/research/sessions?limit=20')
      setSessions(response.data.sessions || [])
    } catch (error) {
      console.error('Error loading research sessions:', error)
      toast({
        title: "Error",
        description: "Failed to load research sessions",
        variant: "destructive"
      })
    } finally {
      setLoadingSessions(false)
    }
  }

  const startResearch = async () => {
    if (!newResearch.query.trim()) {
      toast({
        title: "Missing Query",
        description: "Please enter a research query",
        variant: "destructive"
      })
      return
    }

    try {
      setIsSubmitting(true)

      const response = await api.post('/research/start', newResearch)

      toast({
        title: "Research Started",
        description: `${newResearch.source} research has been started for "${newResearch.query}"`
      })

      // Reset form
      setNewResearch({
        query: '',
        source: 'reddit',
        max_items: 10,
        analysis_depth: 'standard'
      })
      setIsCreateDialogOpen(false)

      // Reload sessions
      loadResearchSessions()

    } catch (error: any) {
      console.error('Error starting research:', error)
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to start research",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const viewResults = async (sessionId: string) => {
    try {
      const response = await api.get(`/research/sessions/${sessionId}`)
      setSelectedResult(response.data)
      setIsResultDialogOpen(true)
    } catch (error) {
      console.error('Error loading research results:', error)
      toast({
        title: "Error",
        description: "Failed to load research results",
        variant: "destructive"
      })
    }
  }

  const deleteSession = async (sessionId: string) => {
    try {
      await api.delete(`/research/sessions/${sessionId}`)
      toast({
        title: "Session Deleted",
        description: "Research session has been deleted"
      })
      loadResearchSessions()
    } catch (error) {
      console.error('Error deleting session:', error)
      toast({
        title: "Error",
        description: "Failed to delete research session",
        variant: "destructive"
      })
    }
  }

  const generateContent = async (contentType: string, platform?: string) => {
    if (!selectedResult) return

    try {
      setIsGeneratingContent(true)

      const response = await api.post('/research/generate-content', {
        research_session_id: selectedResult.id,
        content_type: contentType,
        platform: platform,
        tone: 'professional',
        length: 'medium'
      })

      setGeneratedContent(response.data)

      toast({
        title: "Content Generated",
        description: `${contentType} content has been generated successfully!`
      })

    } catch (error: any) {
      console.error('Error generating content:', error)
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to generate content",
        variant: "destructive"
      })
    } finally {
      setIsGeneratingContent(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'running':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-yellow-100 text-yellow-800'
    }
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Content Intelligence</h1>
            <p className="text-muted-foreground">Loading research tools...</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              </CardHeader>
              <CardContent>
                <div className="h-8 w-16 bg-muted animate-pulse rounded mb-2" />
                <div className="h-3 w-24 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Content Intelligence</h1>
            <p className="text-muted-foreground">Please log in to access research tools.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Content Intelligence</h1>
          <p className="text-muted-foreground">
            Research trending topics and generate content insights
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Research
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Start New Research</DialogTitle>
              <DialogDescription>
                Research trending topics from Reddit, Hacker News, or GitHub
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="query">Research Query</Label>
                <Input
                  id="query"
                  placeholder="e.g., AI automation tools, startup trends, React libraries"
                  value={newResearch.query}
                  onChange={(e) => setNewResearch(prev => ({ ...prev, query: e.target.value }))}
                />
              </div>

              <div>
                <Label htmlFor="source">Source</Label>
                <Select value={newResearch.source} onValueChange={(value) => setNewResearch(prev => ({ ...prev, source: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="reddit">Reddit - Community discussions</SelectItem>
                    <SelectItem value="hackernews">Hacker News - Tech trends</SelectItem>
                    <SelectItem value="github">GitHub - Open source projects</SelectItem>
                    <SelectItem value="google_trends">Google Trends - Search trends</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="max_items">Max Items</Label>
                  <Select value={newResearch.max_items.toString()} onValueChange={(value) => setNewResearch(prev => ({ ...prev, max_items: parseInt(value) }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">5 items</SelectItem>
                      <SelectItem value="10">10 items</SelectItem>
                      <SelectItem value="20">20 items</SelectItem>
                      <SelectItem value="50">50 items</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="analysis_depth">Analysis Depth</Label>
                  <Select value={newResearch.analysis_depth} onValueChange={(value) => setNewResearch(prev => ({ ...prev, analysis_depth: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quick">Quick</SelectItem>
                      <SelectItem value="standard">Standard</SelectItem>
                      <SelectItem value="comprehensive">Comprehensive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={startResearch} disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Start Research
                    </>
                  )}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Research Sessions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Research Sessions</CardTitle>
              <CardDescription>Your recent research activities</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadResearchSessions}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loadingSessions ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4 p-4 border rounded-lg">
                  <div className="h-8 w-8 bg-muted animate-pulse rounded" />
                  <div className="flex-1">
                    <div className="h-4 w-48 bg-muted animate-pulse rounded mb-2" />
                    <div className="h-3 w-32 bg-muted animate-pulse rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8">
              <Search className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No research sessions yet</h3>
              <p className="text-muted-foreground mb-4">
                Start your first research to discover trending topics and insights.
              </p>
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Start Research
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => {
                const SourceIcon = sourceIcons[session.source as keyof typeof sourceIcons]
                return (
                  <div key={session.id} className="flex items-center space-x-4 p-4 border rounded-lg hover:bg-muted/50">
                    <div className="flex-shrink-0">
                      <SourceIcon
                        className="h-8 w-8"
                        style={{ color: sourceColors[session.source as keyof typeof sourceColors] }}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-medium truncate">{session.query}</h4>
                        <Badge className={getStatusColor(session.status)}>
                          {getStatusIcon(session.status)}
                          <span className="ml-1">{session.status}</span>
                        </Badge>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span className="capitalize">{session.source}</span>
                        <span>{session.results_count} results</span>
                        <span>{new Date(session.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {session.status === 'completed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => viewResults(session.id)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => deleteSession(session.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Dialog */}
      <Dialog open={isResultDialogOpen} onOpenChange={setIsResultDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Research Results: {selectedResult?.query}</DialogTitle>
            <DialogDescription>
              {selectedResult?.source} research completed with {selectedResult?.results_count} results
            </DialogDescription>
          </DialogHeader>

          {selectedResult && (
            <Tabs defaultValue="insights" className="w-full">
              <TabsList>
                <TabsTrigger value="insights">Insights</TabsTrigger>
                <TabsTrigger value="raw-data">Raw Data</TabsTrigger>
                <TabsTrigger value="generate">Generate Content</TabsTrigger>
              </TabsList>

              <TabsContent value="insights" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>AI-Generated Insights</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2">Summary</h4>
                        <p className="text-sm text-muted-foreground">
                          {selectedResult.insights?.summary || 'No summary available'}
                        </p>
                      </div>

                      {selectedResult.insights?.key_themes && (
                        <div>
                          <h4 className="font-semibold mb-2">Key Themes</h4>
                          <div className="flex flex-wrap gap-2">
                            {selectedResult.insights.key_themes.map((theme: string, index: number) => (
                              <Badge key={index} variant="secondary">{theme}</Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {selectedResult.insights?.recommendations && (
                        <div>
                          <h4 className="font-semibold mb-2">Recommendations</h4>
                          <ul className="list-disc list-inside space-y-1">
                            {selectedResult.insights.recommendations.map((rec: string, index: number) => (
                              <li key={index} className="text-sm text-muted-foreground">{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="raw-data" className="space-y-4">
                <div className="grid gap-4">
                  {selectedResult.raw_data?.map((item: any, index: number) => (
                    <Card key={index}>
                      <CardContent className="pt-4">
                        <div className="space-y-2">
                          <h4 className="font-medium">{item.title || item.name || 'Untitled'}</h4>
                          {item.url && (
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline text-sm"
                            >
                              View Source
                            </a>
                          )}
                          {item.content && (
                            <p className="text-sm text-muted-foreground line-clamp-3">
                              {item.content}
                            </p>
                          )}
                          <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                            {item.score && <span>Score: {item.score}</span>}
                            {item.comments && <span>Comments: {item.comments}</span>}
                            {item.stars && <span>Stars: {item.stars}</span>}
                            {item.language && <span>Language: {item.language}</span>}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="generate" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Generate Content from Research</CardTitle>
                    <CardDescription>
                      Create social media posts, articles, or summaries based on your research insights
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-2">
                      <Button
                        onClick={() => generateContent('post', 'linkedin')}
                        disabled={isGeneratingContent}
                        className="h-20 flex-col space-y-2"
                      >
                        <MessageSquare className="h-6 w-6" />
                        <span>LinkedIn Post</span>
                      </Button>

                      <Button
                        onClick={() => generateContent('post', 'twitter')}
                        disabled={isGeneratingContent}
                        className="h-20 flex-col space-y-2"
                        variant="outline"
                      >
                        <MessageSquare className="h-6 w-6" />
                        <span>Twitter Post</span>
                      </Button>

                      <Button
                        onClick={() => generateContent('thread', 'twitter')}
                        disabled={isGeneratingContent}
                        className="h-20 flex-col space-y-2"
                        variant="outline"
                      >
                        <MessageSquare className="h-6 w-6" />
                        <span>Twitter Thread</span>
                      </Button>

                      <Button
                        onClick={() => generateContent('article')}
                        disabled={isGeneratingContent}
                        className="h-20 flex-col space-y-2"
                        variant="outline"
                      >
                        <BarChart3 className="h-6 w-6" />
                        <span>Article</span>
                      </Button>

                      <Button
                        onClick={() => generateContent('summary')}
                        disabled={isGeneratingContent}
                        className="h-20 flex-col space-y-2"
                        variant="outline"
                      >
                        <TrendingUp className="h-6 w-6" />
                        <span>Summary</span>
                      </Button>
                    </div>

                    {isGeneratingContent && (
                      <div className="flex items-center justify-center py-8">
                        <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                        <span>Generating content...</span>
                      </div>
                    )}

                    {generatedContent && (
                      <div className="mt-6">
                        <Card>
                          <CardHeader>
                            <CardTitle>{generatedContent.title}</CardTitle>
                            <CardDescription>
                              Generated {generatedContent.content_type} content
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-4">
                              <Textarea
                                value={generatedContent.content}
                                readOnly
                                className="min-h-[200px]"
                              />
                              <div className="flex space-x-2">
                                <Button
                                  onClick={() => {
                                    navigator.clipboard.writeText(generatedContent.content)
                                    toast({
                                      title: "Copied!",
                                      description: "Content copied to clipboard"
                                    })
                                  }}
                                  variant="outline"
                                  size="sm"
                                >
                                  Copy to Clipboard
                                </Button>
                                <Button
                                  onClick={() => {
                                    // TODO: Integrate with social posting API
                                    toast({
                                      title: "Coming Soon",
                                      description: "Direct posting integration coming soon!"
                                    })
                                  }}
                                  size="sm"
                                >
                                  Post to Social Media
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
