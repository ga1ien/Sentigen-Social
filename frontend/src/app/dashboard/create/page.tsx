"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { RichTextEditor } from "@/components/editor/rich-text-editor"
import { useToast } from "@/hooks/use-toast"
import { 
  Wand2, 
  Send, 
  Save, 
  Calendar, 
  Image, 
  Video, 
  Sparkles,
  Twitter,
  Linkedin,
  Facebook,
  Instagram,
  Youtube,
  Clock,
  Target,
  Palette
} from "lucide-react"

const platforms = [
  { id: 'twitter', name: 'Twitter/X', icon: Twitter, color: 'bg-black text-white' },
  { id: 'linkedin', name: 'LinkedIn', icon: Linkedin, color: 'bg-blue-600 text-white' },
  { id: 'facebook', name: 'Facebook', icon: Facebook, color: 'bg-blue-500 text-white' },
  { id: 'instagram', name: 'Instagram', icon: Instagram, color: 'bg-gradient-to-r from-purple-500 to-pink-500 text-white' },
  { id: 'youtube', name: 'YouTube', icon: Youtube, color: 'bg-red-600 text-white' },
]

const contentTypes = [
  { id: 'text', name: 'Text Post', description: 'Simple text-based content' },
  { id: 'image', name: 'Image Post', description: 'Post with images' },
  { id: 'video', name: 'Video Post', description: 'Post with video content' },
  { id: 'carousel', name: 'Carousel', description: 'Multiple images/slides' },
]

const tones = [
  'Professional', 'Casual', 'Friendly', 'Authoritative', 'Humorous', 
  'Inspirational', 'Educational', 'Promotional', 'Conversational'
]

export default function CreatePostPage() {
  const [content, setContent] = useState('')
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
  const [contentType, setContentType] = useState('text')
  const [tone, setTone] = useState('professional')
  const [aiPrompt, setAiPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [scheduledDate, setScheduledDate] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  
  const router = useRouter()
  const { toast } = useToast()

  const handlePlatformToggle = (platformId: string) => {
    setSelectedPlatforms(prev => 
      prev.includes(platformId) 
        ? prev.filter(id => id !== platformId)
        : [...prev, platformId]
    )
  }

  const handleGenerateContent = async () => {
    if (!aiPrompt.trim()) {
      toast({
        title: "Prompt Required",
        description: "Please enter a prompt for AI content generation.",
        variant: "destructive"
      })
      return
    }

    if (selectedPlatforms.length === 0) {
      toast({
        title: "Platform Required",
        description: "Please select at least one platform.",
        variant: "destructive"
      })
      return
    }

    setIsGenerating(true)
    
    try {
      const { apiClient } = await import('@/lib/api')
      
      const response = await apiClient.generateContent({
        prompt: aiPrompt,
        content_type: contentType,
        platforms: selectedPlatforms,
        tone: tone,
        length: 'medium',
        include_hashtags: true,
        include_emojis: false,
        ai_provider: 'anthropic'
      })

      if (response.data?.variations?.length > 0) {
        setContent(response.data.variations[0].content)
        
        toast({
          title: "Content Generated!",
          description: "AI has generated optimized content for your selected platforms.",
        })
      } else {
        throw new Error('No content generated')
      }
    } catch (error) {
      console.error('Content generation error:', error)
      
      // Fallback to mock content if API fails
      const mockContent = `🚀 ${aiPrompt}

Here's some AI-generated content that's optimized for ${selectedPlatforms.join(', ')}. This content maintains a ${tone.toLowerCase()} tone and is designed to engage your audience effectively.

Key points:
• Engaging hook to capture attention
• Valuable insights for your audience  
• Clear call-to-action
• Relevant hashtags for discoverability

#AI #ContentCreation #SocialMedia #Innovation`

      setContent(mockContent)
      
      toast({
        title: "Content Generated (Demo Mode)",
        description: "Using demo content. Connect your backend API for real AI generation.",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()])
      setNewTag('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const handleSaveDraft = async () => {
    // Mock save - in real app, this would call the backend API
    toast({
      title: "Draft Saved",
      description: "Your post has been saved as a draft.",
    })
  }

  const handleSchedulePost = async () => {
    if (!content.trim()) {
      toast({
        title: "Content Required",
        description: "Please add some content to your post.",
        variant: "destructive"
      })
      return
    }

    if (selectedPlatforms.length === 0) {
      toast({
        title: "Platform Required",
        description: "Please select at least one platform.",
        variant: "destructive"
      })
      return
    }

    // Mock schedule - in real app, this would call the backend API
    toast({
      title: "Post Scheduled",
      description: `Your post has been scheduled for ${selectedPlatforms.join(', ')}.`,
    })
    
    router.push('/dashboard/calendar')
  }

  const handlePublishNow = async () => {
    if (!content.trim()) {
      toast({
        title: "Content Required",
        description: "Please add some content to your post.",
        variant: "destructive"
      })
      return
    }

    if (selectedPlatforms.length === 0) {
      toast({
        title: "Platform Required",
        description: "Please select at least one platform.",
        variant: "destructive"
      })
      return
    }

    try {
      const { apiClient } = await import('@/lib/api')
      
      // Create the post
      const createResponse = await apiClient.createPost({
        content,
        content_type: contentType,
        platforms: selectedPlatforms,
        tags,
      })

      if (createResponse.data?.post?.id) {
        // Publish the post immediately
        await apiClient.publishPost(createResponse.data.post.id)
        
        toast({
          title: "Post Published",
          description: `Your post has been published to ${selectedPlatforms.join(', ')}.`,
        })
        
        router.push('/dashboard')
      }
    } catch (error) {
      console.error('Publish error:', error)
      
      toast({
        title: "Publish Failed (Demo Mode)",
        description: "Connect your backend API for real publishing. Demo mode active.",
        variant: "destructive"
      })
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Create Post</h1>
          <p className="text-muted-foreground">
            Create engaging content with AI assistance and publish across platforms
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleSaveDraft}>
            <Save className="mr-2 h-4 w-4" />
            Save Draft
          </Button>
          <Button onClick={handlePublishNow}>
            <Send className="mr-2 h-4 w-4" />
            Publish Now
          </Button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Content Generation */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Sparkles className="mr-2 h-5 w-5" />
                AI Content Generation
              </CardTitle>
              <CardDescription>
                Generate engaging content with AI assistance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="ai-prompt">Content Prompt</Label>
                <Input
                  id="ai-prompt"
                  placeholder="e.g., Write a post about productivity tips for remote workers"
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Tone</Label>
                  <Select value={tone} onValueChange={setTone}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {tones.map((t) => (
                        <SelectItem key={t} value={t.toLowerCase()}>
                          {t}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label>Content Type</Label>
                  <Select value={contentType} onValueChange={setContentType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {contentTypes.map((type) => (
                        <SelectItem key={type.id} value={type.id}>
                          {type.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button 
                onClick={handleGenerateContent} 
                disabled={isGenerating}
                className="w-full"
              >
                <Wand2 className="mr-2 h-4 w-4" />
                {isGenerating ? 'Generating...' : 'Generate Content'}
              </Button>
            </CardContent>
          </Card>

          {/* Rich Text Editor */}
          <Card>
            <CardHeader>
              <CardTitle>Content Editor</CardTitle>
              <CardDescription>
                Write and format your post content
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RichTextEditor
                content={content}
                onChange={setContent}
                placeholder="Start writing your post or use AI generation above..."
                maxLength={2000}
                platforms={selectedPlatforms}
              />
            </CardContent>
          </Card>

          {/* Media Upload */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Image className="mr-2 h-5 w-5" />
                Media Assets
              </CardTitle>
              <CardDescription>
                Add images, videos, or other media to your post
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
                <div className="flex flex-col items-center space-y-2">
                  <Image className="h-8 w-8 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Drag and drop files here, or click to browse
                  </p>
                  <Button variant="outline" size="sm">
                    Choose Files
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Platform Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Target className="mr-2 h-5 w-5" />
                Platforms
              </CardTitle>
              <CardDescription>
                Select where to publish your content
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {platforms.map((platform) => {
                const Icon = platform.icon
                const isSelected = selectedPlatforms.includes(platform.id)
                
                return (
                  <div
                    key={platform.id}
                    className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      isSelected ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/50'
                    }`}
                    onClick={() => handlePlatformToggle(platform.id)}
                  >
                    <Checkbox
                      checked={isSelected}
                      onChange={() => handlePlatformToggle(platform.id)}
                    />
                    <div className={`p-2 rounded ${platform.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="font-medium">{platform.name}</span>
                  </div>
                )
              })}
            </CardContent>
          </Card>

          {/* Scheduling */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Clock className="mr-2 h-5 w-5" />
                Scheduling
              </CardTitle>
              <CardDescription>
                Schedule your post for optimal timing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="schedule-date">Schedule Date & Time</Label>
                <Input
                  id="schedule-date"
                  type="datetime-local"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                />
              </div>
              
              <Button variant="outline" className="w-full">
                <Calendar className="mr-2 h-4 w-4" />
                View Calendar
              </Button>
              
              <Button 
                onClick={handleSchedulePost}
                className="w-full"
                variant="secondary"
              >
                <Calendar className="mr-2 h-4 w-4" />
                Schedule Post
              </Button>
            </CardContent>
          </Card>

          {/* Tags */}
          <Card>
            <CardHeader>
              <CardTitle>Tags</CardTitle>
              <CardDescription>
                Add tags to organize your content
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Input
                  placeholder="Add tag..."
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                />
                <Button onClick={handleAddTag} size="sm">
                  Add
                </Button>
              </div>
              
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <Badge
                      key={tag}
                      variant="secondary"
                      className="cursor-pointer"
                      onClick={() => handleRemoveTag(tag)}
                    >
                      {tag} ×
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
