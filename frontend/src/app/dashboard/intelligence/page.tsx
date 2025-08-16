"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { 
  Brain, 
  TrendingUp, 
  RefreshCw, 
  Settings, 
  Play, 
  Pause, 
  Calendar,
  Eye,
  Heart,
  MessageCircle,
  Share,
  Chrome,
  Zap,
  Target,
  Clock,
  Users,
  BarChart3,
  Lightbulb,
  Search,
  Filter,
  Download,
  ExternalLink
} from 'lucide-react'

interface ContentInsight {
  id: string
  platform: string
  title: string
  content: string
  url: string
  engagement_score: number
  trending_topics: string[]
  sentiment: string
  author?: string
  extracted_at: string
}

interface ContentRecommendation {
  id: string
  title: string
  description: string
  platforms: string[]
  estimated_engagement: string
  content_type: string
  keywords: string[]
  target_audience: string
  content_angle: string
}

interface ScanConfig {
  platforms: string[]
  search_queries: string[]
  time_window_hours: number
  max_posts_per_platform: number
}

const platformIcons = {
  reddit: '🔴',
  linkedin: '💼',
  twitter: '🐦',
  hackernews: '🟠',
  producthunt: '🚀',
  medium: '📝',
  'dev.to': '👨‍💻',
  youtube: '📺'
}

const platformColors = {
  reddit: '#FF4500',
  linkedin: '#0077B5',
  twitter: '#1DA1F2',
  hackernews: '#FF6600',
  producthunt: '#DA552F',
  medium: '#00AB6C',
  'dev.to': '#0A0A0A',
  youtube: '#FF0000'
}

export default function ContentIntelligencePage() {
  const [insights, setInsights] = useState<ContentInsight[]>([])
  const [recommendations, setRecommendations] = useState<ContentRecommendation[]>([])
  const [trendingTopics, setTrendingTopics] = useState<Record<string, number>>({})
  const [engagementPatterns, setEngagementPatterns] = useState<Record<string, unknown>>({})
  const [isScanning, setIsScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)
  const [scheduledScans, setScheduledScans] = useState<Record<string, unknown>[]>([])
  const [chromeMcpStatus, setChromeMcpStatus] = useState<'connected' | 'disconnected' | 'unknown'>('unknown')
  
  // Scan configuration
  const [scanConfig, setScanConfig] = useState<ScanConfig>({
    platforms: ['reddit', 'linkedin', 'twitter'],
    search_queries: ['AI', 'artificial intelligence', 'machine learning', 'automation'],
    time_window_hours: 24,
    max_posts_per_platform: 20
  })
  
  const { toast } = useToast()

  useEffect(() => {
    loadInitialData()
    checkChromeMcpStatus()
  }, [])

  const loadInitialData = async () => {
    try {
      // Load recent insights
      const insightsResponse = await fetch('/api/content-intelligence/insights/trending?limit=20')
      if (insightsResponse.ok) {
        const insightsData = await insightsResponse.json()
        setInsights(insightsData.insights)
      }

      // Load recommendations
      const recResponse = await fetch('/api/content-intelligence/recommendations?limit=10')
      if (recResponse.ok) {
        const recData = await recResponse.json()
        setRecommendations(recData.recommendations)
      }

      // Load trending topics
      const topicsResponse = await fetch('/api/content-intelligence/analytics/trending-topics')
      if (topicsResponse.ok) {
        const topicsData = await topicsResponse.json()
        const topics = topicsData.trending_topics.reduce((acc: Record<string, number>, item: { topic: string; count: number }) => {
          acc[item.topic] = item.count
          return acc
        }, {})
        setTrendingTopics(topics)
      }

      // Load engagement patterns
      const patternsResponse = await fetch('/api/content-intelligence/analytics/engagement-patterns')
      if (patternsResponse.ok) {
        const patternsData = await patternsResponse.json()
        setEngagementPatterns(patternsData)
      }

      // Load scheduled scans
      const scheduledResponse = await fetch('/api/content-intelligence/scheduled-scans')
      if (scheduledResponse.ok) {
        const scheduledData = await scheduledResponse.json()
        setScheduledScans(scheduledData.scheduled_scans)
      }

    } catch (error) {
      console.error('Failed to load initial data:', error)
    }
  }

  const checkChromeMcpStatus = async () => {
    try {
      const response = await fetch('/api/content-intelligence/health')
      if (response.ok) {
        const data = await response.json()
        setChromeMcpStatus(data.chrome_mcp_connected ? 'connected' : 'disconnected')
      } else {
        setChromeMcpStatus('disconnected')
      }
    } catch (error) {
      setChromeMcpStatus('disconnected')
    }
  }

  const triggerScan = async () => {
    setIsScanning(true)
    setScanProgress(0)
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setScanProgress(prev => Math.min(prev + 10, 90))
      }, 1000)

      const response = await fetch('/api/content-intelligence/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scanConfig)
      })

      clearInterval(progressInterval)
      setScanProgress(100)

      if (response.ok) {
        const data = await response.json()
        
        toast({
          title: "Scan Completed!",
          description: `Found ${data.results.total_insights} insights across ${scanConfig.platforms.length} platforms`,
        })

        // Reload data
        await loadInitialData()
      } else {
        throw new Error('Scan failed')
      }
    } catch (error) {
      toast({
        title: "Scan Failed",
        description: "Failed to scan platforms. Check Chrome MCP connection.",
        variant: "destructive"
      })
    } finally {
      setIsScanning(false)
      setScanProgress(0)
    }
  }

  const scheduleRecurringScan = async () => {
    try {
      const response = await fetch('/api/content-intelligence/schedule-scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platforms: scanConfig.platforms,
          search_queries: scanConfig.search_queries,
          interval_hours: 6,
          max_posts_per_platform: scanConfig.max_posts_per_platform
        })
      })

      if (response.ok) {
        const data = await response.json()
        toast({
          title: "Scan Scheduled",
          description: `Recurring scan scheduled every 6 hours for ${scanConfig.platforms.length} platforms`,
        })
        
        // Reload scheduled scans
        const scheduledResponse = await fetch('/api/content-intelligence/scheduled-scans')
        if (scheduledResponse.ok) {
          const scheduledData = await scheduledResponse.json()
          setScheduledScans(scheduledData.scheduled_scans)
        }
      }
    } catch (error) {
      toast({
        title: "Scheduling Failed",
        description: "Failed to schedule recurring scan",
        variant: "destructive"
      })
    }
  }

  const generateRecommendations = async () => {
    try {
      const response = await fetch('/api/content-intelligence/recommendations?regenerate=true')
      if (response.ok) {
        const data = await response.json()
        setRecommendations(data.recommendations)
        
        toast({
          title: "Recommendations Updated",
          description: `Generated ${data.recommendations.length} new content recommendations`,
        })
      }
    } catch (error) {
      toast({
        title: "Generation Failed",
        description: "Failed to generate new recommendations",
        variant: "destructive"
      })
    }
  }

  const handlePlatformToggle = (platform: string) => {
    setScanConfig(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }))
  }

  const formatEngagementScore = (score: number) => {
    if (score >= 100) return 'High'
    if (score >= 50) return 'Medium'
    return 'Low'
  }

  const getEngagementColor = (score: number) => {
    if (score >= 100) return 'text-green-600'
    if (score >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="h-8 w-8" />
            Content Intelligence
          </h1>
          <p className="text-muted-foreground">
            AI-powered insights from social media monitoring via Chrome MCP
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge 
            variant={chromeMcpStatus === 'connected' ? 'default' : 'destructive'}
            className="flex items-center gap-1"
          >
            <Chrome className="h-3 w-3" />
            Chrome MCP {chromeMcpStatus}
          </Badge>
          <Button onClick={generateRecommendations} variant="outline">
            <Lightbulb className="mr-2 h-4 w-4" />
            Generate Ideas
          </Button>
          <Button onClick={triggerScan} disabled={isScanning}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isScanning ? 'animate-spin' : ''}`} />
            {isScanning ? 'Scanning...' : 'Scan Now'}
          </Button>
        </div>
      </div>

      {/* Scan Progress */}
      {isScanning && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Scanning {scanConfig.platforms.length} platforms...</span>
                <span>{scanProgress}%</span>
              </div>
              <Progress value={scanProgress} className="w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Insights</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{insights.length}</div>
            <p className="text-xs text-muted-foreground">
              From {Object.keys(trendingTopics).length} trending topics
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recommendations</CardTitle>
            <Lightbulb className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recommendations.length}</div>
            <p className="text-xs text-muted-foreground">
              AI-generated content ideas
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled Scans</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scheduledScans.length}</div>
            <p className="text-xs text-muted-foreground">
              Automated monitoring
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Engagement</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {insights.length > 0 
                ? Math.round(insights.reduce((sum, i) => sum + i.engagement_score, 0) / insights.length)
                : 0
              }
            </div>
            <p className="text-xs text-muted-foreground">
              Across all platforms
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="insights" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="insights">Insights</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="trending">Trending</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="insights" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Latest Content Insights</CardTitle>
              <CardDescription>
                High-engagement content discovered across social platforms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {insights.map((insight) => (
                  <div key={insight.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">{platformIcons[insight.platform as keyof typeof platformIcons]}</span>
                          <Badge variant="outline">{insight.platform}</Badge>
                          <Badge 
                            variant={insight.sentiment === 'positive' ? 'default' : 
                                   insight.sentiment === 'negative' ? 'destructive' : 'secondary'}
                          >
                            {insight.sentiment}
                          </Badge>
                        </div>
                        <h3 className="font-semibold mb-2">{insight.title}</h3>
                        <p className="text-sm text-muted-foreground mb-3">
                          {insight.content.substring(0, 200)}...
                        </p>
                        <div className="flex items-center gap-4 text-sm">
                          <span className={`font-medium ${getEngagementColor(insight.engagement_score)}`}>
                            Engagement: {formatEngagementScore(insight.engagement_score)}
                          </span>
                          {insight.author && (
                            <span>By: {insight.author}</span>
                          )}
                          <span>{new Date(insight.extracted_at).toLocaleDateString()}</span>
                        </div>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {insight.trending_topics.slice(0, 5).map((topic) => (
                            <Badge key={topic} variant="outline" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" asChild>
                          <a href={insight.url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        </Button>
                        <Button variant="outline" size="sm">
                          Create Content
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>AI Content Recommendations</CardTitle>
              <CardDescription>
                Data-driven content ideas based on trending insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recommendations.map((rec, idx) => (
                  <div key={rec.id || idx} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-semibold mb-2">{rec.title}</h3>
                        <p className="text-sm text-muted-foreground mb-3">
                          {rec.description}
                        </p>
                        <div className="flex items-center gap-4 mb-3">
                          <Badge variant="outline">{rec.content_type}</Badge>
                          <Badge 
                            variant={rec.estimated_engagement === 'high' ? 'default' : 
                                   rec.estimated_engagement === 'low' ? 'secondary' : 'outline'}
                          >
                            {rec.estimated_engagement} engagement
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            Target: {rec.target_audience}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium">Platforms:</span>
                          {rec.platforms.map((platform) => (
                            <Badge key={platform} variant="outline" className="text-xs">
                              {platformIcons[platform as keyof typeof platformIcons]} {platform}
                            </Badge>
                          ))}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {rec.keywords.slice(0, 6).map((keyword) => (
                            <Badge key={keyword} variant="outline" className="text-xs">
                              #{keyword}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Button>
                        Create Post
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trending" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Trending Topics</CardTitle>
                <CardDescription>
                  Most mentioned topics across platforms
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(trendingTopics)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 10)
                    .map(([topic, count]) => (
                      <div key={topic} className="flex items-center justify-between">
                        <span className="font-medium">{topic}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-muted rounded-full h-2">
                            <div 
                              className="bg-primary h-2 rounded-full" 
                              style={{ 
                                width: `${Math.min((count / Math.max(...Object.values(trendingTopics))) * 100, 100)}%` 
                              }}
                            />
                          </div>
                          <span className="text-sm text-muted-foreground w-8">{count}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Platform Distribution</CardTitle>
                <CardDescription>
                  Content sources by platform
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={Object.entries(
                        insights.reduce((acc, insight) => {
                          acc[insight.platform] = (acc[insight.platform] || 0) + 1
                          return acc
                        }, {} as Record<string, number>)
                      ).map(([platform, count]) => ({ platform, count }))}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                      label={({ platform, count }) => `${platform}: ${count}`}
                    >
                      {Object.keys(platformColors).map((platform, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={platformColors[platform as keyof typeof platformColors]} 
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Engagement Analytics</CardTitle>
              <CardDescription>
                Performance metrics across platforms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={Object.entries(engagementPatterns.avg_engagement_by_platform || {}).map(([platform, avg]) => ({ platform, avg }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="platform" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="avg" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Scan Configuration</CardTitle>
                <CardDescription>
                  Configure platforms and search parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Platforms to Monitor</Label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {Object.keys(platformIcons).map((platform) => (
                      <div key={platform} className="flex items-center space-x-2">
                        <Switch
                          checked={scanConfig.platforms.includes(platform)}
                          onCheckedChange={() => handlePlatformToggle(platform)}
                        />
                        <span className="text-sm">
                          {platformIcons[platform as keyof typeof platformIcons]} {platform}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label htmlFor="search-queries">Search Queries</Label>
                  <Textarea
                    id="search-queries"
                    placeholder="Enter search queries, one per line"
                    value={scanConfig.search_queries.join('\n')}
                    onChange={(e) => setScanConfig(prev => ({
                      ...prev,
                      search_queries: e.target.value.split('\n').filter(q => q.trim())
                    }))}
                    rows={4}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="time-window">Time Window (hours)</Label>
                    <Input
                      id="time-window"
                      type="number"
                      value={scanConfig.time_window_hours}
                      onChange={(e) => setScanConfig(prev => ({
                        ...prev,
                        time_window_hours: parseInt(e.target.value) || 24
                      }))}
                    />
                  </div>
                  <div>
                    <Label htmlFor="max-posts">Max Posts per Platform</Label>
                    <Input
                      id="max-posts"
                      type="number"
                      value={scanConfig.max_posts_per_platform}
                      onChange={(e) => setScanConfig(prev => ({
                        ...prev,
                        max_posts_per_platform: parseInt(e.target.value) || 20
                      }))}
                    />
                  </div>
                </div>

                <Button onClick={scheduleRecurringScan} className="w-full">
                  <Calendar className="mr-2 h-4 w-4" />
                  Schedule Recurring Scan
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Scheduled Scans</CardTitle>
                <CardDescription>
                  Manage automated monitoring
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {scheduledScans.map((scan) => (
                    <div key={scan.scan_id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">
                          {scan.platforms.join(', ')}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Next run: {new Date(scan.next_run).toLocaleString()}
                        </div>
                      </div>
                      <Badge variant={scan.status === 'scheduled' ? 'default' : 'secondary'}>
                        {scan.status}
                      </Badge>
                    </div>
                  ))}
                  {scheduledScans.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      No scheduled scans configured
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
