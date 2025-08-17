'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  Play, 
  Pause, 
  Download, 
  Share2, 
  Plus, 
  Settings, 
  Video, 
  FileText, 
  Zap,
  Clock,
  User,
  Mic,
  Image as ImageIcon,
  Trash2,
  Edit,
  Star,
  BarChart3,
  RefreshCw
} from 'lucide-react'
import { toast } from 'sonner'

// Types
interface AvatarProfile {
  id: number
  name: string
  avatar_id: string
  voice_id: string
  avatar_type: 'talking_photo' | 'avatar' | 'custom'
  description?: string
  preview_url?: string
  is_default: boolean
  display_order: number
  created_at: string
}

interface ScriptGeneration {
  id: number
  topic: string
  script: string
  target_audience: string
  video_style: string
  duration_target: number
  quality_score: number
  created_at: string
}

interface VideoGeneration {
  id: number
  heygen_video_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  video_url?: string
  thumbnail_url?: string
  aspect_ratio: 'landscape' | 'portrait' | 'square'
  duration?: number
  error_message?: string
  created_at: string
  completed_at?: string
}

interface UserLimits {
  subscription_tier: string
  monthly_limit: number
  videos_this_month: number
  remaining_videos: number
  is_admin: boolean
}

export default function AvatarsPage() {
  // State
  const [activeTab, setActiveTab] = useState('overview')
  const [avatarProfiles, setAvatarProfiles] = useState<AvatarProfile[]>([])
  const [scripts, setScripts] = useState<ScriptGeneration[]>([])
  const [videos, setVideos] = useState<VideoGeneration[]>([])
  const [userLimits, setUserLimits] = useState<UserLimits | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedAvatar, setSelectedAvatar] = useState<AvatarProfile | null>(null)
  
  // Script generation state
  const [scriptForm, setScriptForm] = useState({
    topic: '',
    target_audience: 'general audience',
    video_style: 'professional',
    duration_target: 60,
    additional_context: ''
  })
  const [generatingScript, setGeneratingScript] = useState(false)
  
  // Video creation state
  const [videoForm, setVideoForm] = useState({
    script_id: null as number | null,
    script_text: '',
    profile_id: null as number | null,
    aspect_ratio: 'landscape' as 'landscape' | 'portrait' | 'square'
  })
  const [creatingVideo, setCreatingVideo] = useState(false)

  // Load data on component mount
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Load all data in parallel
      const [avatarsRes, scriptsRes, videosRes, limitsRes] = await Promise.all([
        fetch('/api/avatars/profiles'),
        fetch('/api/avatars/scripts'),
        fetch('/api/avatars/videos'),
        fetch('/api/avatars/limits')
      ])

      const [avatarsData, scriptsData, videosData, limitsData] = await Promise.all([
        avatarsRes.json(),
        scriptsRes.json(),
        videosRes.json(),
        limitsRes.json()
      ])

      setAvatarProfiles(avatarsData.avatars || [])
      setScripts(scriptsData || [])
      setVideos(videosData || [])
      setUserLimits(limitsData)
      
      // Set default avatar
      const defaultAvatar = avatarsData.avatars?.find((a: AvatarProfile) => a.is_default)
      if (defaultAvatar) {
        setSelectedAvatar(defaultAvatar)
        setVideoForm(prev => ({ ...prev, profile_id: defaultAvatar.id }))
      }
      
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load avatar data')
    } finally {
      setLoading(false)
    }
  }

  const generateScript = async () => {
    try {
      setGeneratingScript(true)
      
      const response = await fetch('/api/avatars/scripts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scriptForm)
      })
      
      if (!response.ok) throw new Error('Failed to generate script')
      
      const result = await response.json()
      
      // Add to scripts list
      const newScript: ScriptGeneration = {
        id: result.script_id,
        topic: scriptForm.topic,
        script: result.script,
        target_audience: scriptForm.target_audience,
        video_style: scriptForm.video_style,
        duration_target: scriptForm.duration_target,
        quality_score: result.quality_score,
        created_at: new Date().toISOString()
      }
      
      setScripts(prev => [newScript, ...prev])
      
      // Set as current script for video creation
      setVideoForm(prev => ({
        ...prev,
        script_id: result.script_id,
        script_text: result.script
      }))
      
      toast.success('Script generated successfully!')
      setActiveTab('create-video')
      
    } catch (error) {
      console.error('Failed to generate script:', error)
      toast.error('Failed to generate script')
    } finally {
      setGeneratingScript(false)
    }
  }

  const createVideo = async () => {
    try {
      setCreatingVideo(true)
      
      const response = await fetch('/api/avatars/videos/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(videoForm)
      })
      
      if (!response.ok) throw new Error('Failed to create video')
      
      const result = await response.json()
      
      // Add to videos list
      const newVideo: VideoGeneration = {
        id: result.video_id,
        heygen_video_id: result.heygen_video_id,
        status: result.status,
        aspect_ratio: videoForm.aspect_ratio,
        created_at: new Date().toISOString()
      }
      
      setVideos(prev => [newVideo, ...prev])
      
      toast.success('Video creation started!')
      setActiveTab('videos')
      
      // Refresh user limits
      const limitsRes = await fetch('/api/avatars/limits')
      const limitsData = await limitsRes.json()
      setUserLimits(limitsData)
      
    } catch (error) {
      console.error('Failed to create video:', error)
      toast.error('Failed to create video')
    } finally {
      setCreatingVideo(false)
    }
  }

  const syncHeyGenAvatars = async () => {
    try {
      const response = await fetch('/api/avatars/sync-heygen', { method: 'POST' })
      if (!response.ok) throw new Error('Failed to sync avatars')
      
      const result = await response.json()
      toast.success(`Synced ${result.created} new avatars and updated ${result.updated} existing ones`)
      
      // Reload avatar profiles
      const avatarsRes = await fetch('/api/avatars/profiles')
      const avatarsData = await avatarsRes.json()
      setAvatarProfiles(avatarsData.avatars || [])
      
    } catch (error) {
      console.error('Failed to sync avatars:', error)
      toast.error('Failed to sync HeyGen avatars')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500'
      case 'processing': return 'bg-blue-500'
      case 'failed': return 'bg-red-500'
      case 'cancelled': return 'bg-gray-500'
      default: return 'bg-yellow-500'
    }
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'Unknown'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading avatar system...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI Avatars</h1>
          <p className="text-muted-foreground">
            Create engaging videos with AI avatars and generated scripts
          </p>
        </div>
        
        {userLimits && (
          <Card className="w-64">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Video Credits</span>
                <Badge variant={userLimits.remaining_videos > 0 ? 'default' : 'destructive'}>
                  {userLimits.subscription_tier}
                </Badge>
              </div>
              <div className="text-2xl font-bold">
                {userLimits.remaining_videos} / {userLimits.monthly_limit}
              </div>
              <p className="text-xs text-muted-foreground">
                {userLimits.videos_this_month} used this month
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="avatars">Avatars</TabsTrigger>
          <TabsTrigger value="generate-script">Generate Script</TabsTrigger>
          <TabsTrigger value="create-video">Create Video</TabsTrigger>
          <TabsTrigger value="videos">Videos</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Videos</CardTitle>
                <Video className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{videos.length}</div>
                <p className="text-xs text-muted-foreground">
                  {videos.filter(v => v.status === 'completed').length} completed
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Scripts Generated</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{scripts.length}</div>
                <p className="text-xs text-muted-foreground">
                  Avg quality: {scripts.length > 0 ? (scripts.reduce((acc, s) => acc + s.quality_score, 0) / scripts.length * 100).toFixed(0) : 0}%
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avatar Profiles</CardTitle>
                <User className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{avatarProfiles.length}</div>
                <p className="text-xs text-muted-foreground">
                  {avatarProfiles.filter(a => a.is_default).length} default
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Processing</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {videos.filter(v => v.status === 'processing').length}
                </div>
                <p className="text-xs text-muted-foreground">
                  Videos in progress
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Your latest videos and scripts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[...videos.slice(0, 3), ...scripts.slice(0, 2)].sort((a, b) => 
                  new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                ).slice(0, 5).map((item, index) => (
                  <div key={index} className="flex items-center space-x-4">
                    <div className={`w-2 h-2 rounded-full ${'status' in item ? getStatusColor(item.status) : 'bg-blue-500'}`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium">
                        {'status' in item ? `Video: ${item.heygen_video_id}` : `Script: ${item.topic}`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Avatars Tab */}
        <TabsContent value="avatars" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Avatar Profiles</h2>
            <div className="space-x-2">
              <Button onClick={syncHeyGenAvatars} variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Sync HeyGen
              </Button>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Avatar
              </Button>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {avatarProfiles.map((avatar) => (
              <Card key={avatar.id} className={`cursor-pointer transition-all hover:shadow-lg ${selectedAvatar?.id === avatar.id ? 'ring-2 ring-primary' : ''}`}>
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4 mb-4">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={avatar.preview_url} alt={avatar.name} />
                      <AvatarFallback>
                        {avatar.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <h3 className="font-semibold flex items-center">
                        {avatar.name}
                        {avatar.is_default && <Star className="h-4 w-4 ml-2 text-yellow-500" />}
                      </h3>
                      <p className="text-sm text-muted-foreground capitalize">
                        {avatar.avatar_type.replace('_', ' ')}
                      </p>
                    </div>
                  </div>
                  
                  {avatar.description && (
                    <p className="text-sm text-muted-foreground mb-4">
                      {avatar.description}
                    </p>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <div className="flex space-x-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setSelectedAvatar(avatar)}
                      >
                        Select
                      </Button>
                      {avatar.preview_url && (
                        <Button size="sm" variant="outline">
                          <Play className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    <div className="flex space-x-1">
                      <Button size="sm" variant="ghost">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="ghost">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Generate Script Tab */}
        <TabsContent value="generate-script" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Generate AI Script</CardTitle>
              <CardDescription>
                Create engaging video scripts using advanced AI
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="topic">Topic</Label>
                  <Input
                    id="topic"
                    placeholder="Enter your video topic..."
                    value={scriptForm.topic}
                    onChange={(e) => setScriptForm(prev => ({ ...prev, topic: e.target.value }))}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="audience">Target Audience</Label>
                  <Input
                    id="audience"
                    placeholder="e.g., tech entrepreneurs, students..."
                    value={scriptForm.target_audience}
                    onChange={(e) => setScriptForm(prev => ({ ...prev, target_audience: e.target.value }))}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="style">Video Style</Label>
                  <Select value={scriptForm.video_style} onValueChange={(value) => setScriptForm(prev => ({ ...prev, video_style: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="casual">Casual</SelectItem>
                      <SelectItem value="educational">Educational</SelectItem>
                      <SelectItem value="entertaining">Entertaining</SelectItem>
                      <SelectItem value="motivational">Motivational</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="duration">Duration (seconds)</Label>
                  <Input
                    id="duration"
                    type="number"
                    min="15"
                    max="300"
                    value={scriptForm.duration_target}
                    onChange={(e) => setScriptForm(prev => ({ ...prev, duration_target: parseInt(e.target.value) }))}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="context">Additional Context (Optional)</Label>
                <Textarea
                  id="context"
                  placeholder="Any specific requirements, key points to include, or style preferences..."
                  value={scriptForm.additional_context}
                  onChange={(e) => setScriptForm(prev => ({ ...prev, additional_context: e.target.value }))}
                />
              </div>
              
              <Button 
                onClick={generateScript} 
                disabled={!scriptForm.topic || generatingScript}
                className="w-full"
              >
                {generatingScript ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Generating Script...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Generate Script
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Recent Scripts */}
          {scripts.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Scripts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {scripts.slice(0, 3).map((script) => (
                    <div key={script.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold">{script.topic}</h4>
                        <Badge variant="outline">
                          Quality: {(script.quality_score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {script.script.substring(0, 150)}...
                      </p>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{script.target_audience} • {script.video_style}</span>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            setVideoForm(prev => ({
                              ...prev,
                              script_id: script.id,
                              script_text: script.script
                            }))
                            setActiveTab('create-video')
                          }}
                        >
                          Use Script
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Create Video Tab */}
        <TabsContent value="create-video" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Create Video</CardTitle>
              <CardDescription>
                Generate a video using your script and selected avatar
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Script Selection */}
              <div className="space-y-2">
                <Label htmlFor="script">Script</Label>
                <Textarea
                  id="script"
                  placeholder="Enter your script or generate one first..."
                  value={videoForm.script_text}
                  onChange={(e) => setVideoForm(prev => ({ ...prev, script_text: e.target.value }))}
                  rows={6}
                />
              </div>
              
              {/* Avatar Selection */}
              <div className="space-y-2">
                <Label>Avatar</Label>
                <div className="grid gap-3 md:grid-cols-3">
                  {avatarProfiles.slice(0, 6).map((avatar) => (
                    <div
                      key={avatar.id}
                      className={`border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md ${
                        videoForm.profile_id === avatar.id ? 'ring-2 ring-primary' : ''
                      }`}
                      onClick={() => setVideoForm(prev => ({ ...prev, profile_id: avatar.id }))}
                    >
                      <div className="flex items-center space-x-3">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={avatar.preview_url} alt={avatar.name} />
                          <AvatarFallback>
                            {avatar.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{avatar.name}</p>
                          <p className="text-xs text-muted-foreground capitalize">
                            {avatar.avatar_type.replace('_', ' ')}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Video Settings */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="aspect-ratio">Aspect Ratio</Label>
                  <Select value={videoForm.aspect_ratio} onValueChange={(value: 'landscape' | 'portrait' | 'square') => setVideoForm(prev => ({ ...prev, aspect_ratio: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="landscape">Landscape (16:9)</SelectItem>
                      <SelectItem value="portrait">Portrait (9:16)</SelectItem>
                      <SelectItem value="square">Square (1:1)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <Button 
                onClick={createVideo} 
                disabled={!videoForm.script_text || !videoForm.profile_id || creatingVideo || (userLimits?.remaining_videos || 0) <= 0}
                className="w-full"
              >
                {creatingVideo ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Creating Video...
                  </>
                ) : (
                  <>
                    <Video className="h-4 w-4 mr-2" />
                    Create Video ({userLimits?.remaining_videos || 0} credits remaining)
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Videos Tab */}
        <TabsContent value="videos" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Generated Videos</h2>
            <Button onClick={loadData} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {videos.map((video) => (
              <Card key={video.id}>
                <CardContent className="p-6">
                  <div className="aspect-video bg-muted rounded-lg mb-4 flex items-center justify-center">
                    {video.video_url ? (
                      <video 
                        src={video.video_url} 
                        controls 
                        className="w-full h-full rounded-lg"
                        poster={video.thumbnail_url}
                      />
                    ) : (
                      <div className="text-center">
                        <Video className="h-12 w-12 mx-auto mb-2 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground capitalize">
                          {video.status}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge className={getStatusColor(video.status)}>
                        {video.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {video.aspect_ratio}
                      </span>
                    </div>
                    
                    {video.duration && (
                      <p className="text-sm">
                        Duration: {formatDuration(video.duration)}
                      </p>
                    )}
                    
                    <p className="text-xs text-muted-foreground">
                      Created: {new Date(video.created_at).toLocaleDateString()}
                    </p>
                    
                    {video.status === 'processing' && (
                      <Progress value={50} className="w-full" />
                    )}
                    
                    {video.error_message && (
                      <p className="text-xs text-red-500">
                        Error: {video.error_message}
                      </p>
                    )}
                    
                    {video.status === 'completed' && video.video_url && (
                      <div className="flex space-x-2 pt-2">
                        <Button size="sm" variant="outline">
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Share2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          
          {videos.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center">
                <Video className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No videos yet</h3>
                <p className="text-muted-foreground mb-4">
                  Create your first AI-generated video to get started
                </p>
                <Button onClick={() => setActiveTab('generate-script')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Video
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
