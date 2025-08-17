'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Brain,
  Sparkles,
  Image as ImageIcon,
  Video,
  MessageSquare,
  Search,
  Lightbulb,
  Wand2,
  Copy,
  Download,
  RefreshCw,
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface AITool {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  category: 'content' | 'image' | 'video' | 'research' | 'optimization'
  status: 'available' | 'coming-soon' | 'beta'
}

const aiTools: AITool[] = [
  {
    id: 'content-generator',
    name: 'Content Generator',
    description: 'Generate engaging social media posts with AI',
    icon: <MessageSquare className="h-6 w-6" />,
    category: 'content',
    status: 'available'
  },
  {
    id: 'image-generator',
    name: 'Image Generator',
    description: 'Create stunning visuals with GPT-Image-1',
    icon: <ImageIcon className="h-6 w-6" />,
    category: 'image',
    status: 'available'
  },
  {
    id: 'video-generator',
    name: 'Video Generator',
    description: 'Generate videos with HeyGen and Google Veo3',
    icon: <Video className="h-6 w-6" />,
    category: 'video',
    status: 'beta'
  },
  {
    id: 'hashtag-generator',
    name: 'Hashtag Generator',
    description: 'Generate relevant hashtags for your content',
    icon: <Wand2 className="h-6 w-6" />,
    category: 'optimization',
    status: 'available'
  },
  {
    id: 'content-optimizer',
    name: 'Content Optimizer',
    description: 'Optimize your posts for maximum engagement',
    icon: <Sparkles className="h-6 w-6" />,
    category: 'optimization',
    status: 'available'
  },
  {
    id: 'trend-researcher',
    name: 'Trend Researcher',
    description: 'Research trending topics with Perplexity AI',
    icon: <Search className="h-6 w-6" />,
    category: 'research',
    status: 'available'
  },
  {
    id: 'idea-generator',
    name: 'Idea Generator',
    description: 'Generate creative content ideas',
    icon: <Lightbulb className="h-6 w-6" />,
    category: 'content',
    status: 'available'
  }
]

export default function AIToolsPage() {
  const [selectedTool, setSelectedTool] = useState<string>('content-generator')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<string>('')
  const [prompt, setPrompt] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const { toast } = useToast()

  const filteredTools = selectedCategory === 'all'
    ? aiTools
    : aiTools.filter(tool => tool.category === selectedCategory)

  const selectedToolData = aiTools.find(tool => tool.id === selectedTool)

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast({
        title: "Prompt required",
        description: "Please enter a prompt to generate content.",
        variant: "destructive",
      })
      return
    }

    setIsGenerating(true)
    setResult('')

    try {
      // TODO: Implement real AI API calls to backend
      // For now, show a message that this feature is coming soon

      setResult(`🚧 AI ${aiTools.find(t => t.id === selectedTool)?.name} is coming soon!

This feature will be connected to real AI services including:
• OpenAI GPT for content generation
• Advanced trend analysis
• Real-time optimization suggestions

Stay tuned for the full implementation!`)

      toast({
        title: "Feature Coming Soon",
        description: "AI tools will be available in the next update!",
      })
    } catch (error) {
      toast({
        title: "Generation failed",
        description: "There was an error generating your content.",
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result)
    toast({
      title: "Copied to clipboard",
      description: "Generated content copied to clipboard.",
    })
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'available':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Available</Badge>
      case 'beta':
        return <Badge variant="secondary"><AlertCircle className="w-3 h-3 mr-1" />Beta</Badge>
      case 'coming-soon':
        return <Badge variant="outline">Coming Soon</Badge>
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI Tools</h1>
          <p className="text-muted-foreground">
            Supercharge your content creation with AI-powered tools
          </p>
        </div>
        <Badge variant="outline" className="bg-gradient-to-r from-purple-500 to-pink-500 text-white border-0">
          <Brain className="w-4 h-4 mr-1" />
          AI Powered
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tool Selection */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Available Tools</CardTitle>
              <CardDescription>
                Select an AI tool to get started
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="content">Content</SelectItem>
                  <SelectItem value="image">Images</SelectItem>
                  <SelectItem value="video">Videos</SelectItem>
                  <SelectItem value="research">Research</SelectItem>
                  <SelectItem value="optimization">Optimization</SelectItem>
                </SelectContent>
              </Select>

              <div className="space-y-2">
                {filteredTools.map((tool) => (
                  <div
                    key={tool.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedTool === tool.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => setSelectedTool(tool.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="text-primary mt-0.5">
                        {tool.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="font-medium text-sm">{tool.name}</h3>
                          {getStatusBadge(tool.status)}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {tool.description}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tool Interface */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-3">
                <div className="text-primary">
                  {selectedToolData?.icon}
                </div>
                <div>
                  <CardTitle>{selectedToolData?.name}</CardTitle>
                  <CardDescription>{selectedToolData?.description}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Input Section */}
              <div className="space-y-4">
                <div>
                  <Label htmlFor="prompt">Prompt</Label>
                  <Textarea
                    id="prompt"
                    placeholder={`Enter your ${selectedToolData?.name.toLowerCase()} prompt...`}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={4}
                  />
                </div>

                {/* Tool-specific options */}
                {selectedTool === 'content-generator' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Tone</Label>
                      <Select defaultValue="professional">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="professional">Professional</SelectItem>
                          <SelectItem value="casual">Casual</SelectItem>
                          <SelectItem value="friendly">Friendly</SelectItem>
                          <SelectItem value="humorous">Humorous</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Platform</Label>
                      <Select defaultValue="twitter">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="twitter">Twitter</SelectItem>
                          <SelectItem value="linkedin">LinkedIn</SelectItem>
                          <SelectItem value="facebook">Facebook</SelectItem>
                          <SelectItem value="instagram">Instagram</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}

                {selectedTool === 'image-generator' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Style</Label>
                      <Select defaultValue="realistic">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="realistic">Realistic</SelectItem>
                          <SelectItem value="artistic">Artistic</SelectItem>
                          <SelectItem value="cartoon">Cartoon</SelectItem>
                          <SelectItem value="abstract">Abstract</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Size</Label>
                      <Select defaultValue="1024x1024">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1024x1024">Square (1024×1024)</SelectItem>
                          <SelectItem value="1024x1536">Portrait (1024×1536)</SelectItem>
                          <SelectItem value="1536x1024">Landscape (1536×1024)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}

                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating || !prompt.trim()}
                  className="w-full"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Generate with AI
                    </>
                  )}
                </Button>
              </div>

              {/* Results Section */}
              {result && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Generated Result</Label>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm" onClick={copyToClipboard}>
                        <Copy className="h-4 w-4 mr-1" />
                        Copy
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleGenerate}>
                        <RefreshCw className="h-4 w-4 mr-1" />
                        Regenerate
                      </Button>
                    </div>
                  </div>
                  <div className="bg-muted p-4 rounded-lg">
                    <pre className="whitespace-pre-wrap text-sm">{result}</pre>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <CardContent className="p-6 text-center">
            <MessageSquare className="mx-auto h-8 w-8 text-primary mb-3" />
            <h3 className="font-semibold mb-2">Quick Post</h3>
            <p className="text-sm text-muted-foreground">Generate a social media post in seconds</p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <CardContent className="p-6 text-center">
            <ImageIcon className="mx-auto h-8 w-8 text-primary mb-3" />
            <h3 className="font-semibold mb-2">Create Image</h3>
            <p className="text-sm text-muted-foreground">Generate custom images for your posts</p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <CardContent className="p-6 text-center">
            <Search className="mx-auto h-8 w-8 text-primary mb-3" />
            <h3 className="font-semibold mb-2">Research Trends</h3>
            <p className="text-sm text-muted-foreground">Discover what&apos;s trending in your industry</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
