'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Upload,
  Search,
  Filter,
  Grid3X3,
  List,
  Image as ImageIcon,
  Video,
  FileText,
  Download,
  Trash2,
  Eye,
  Copy,
  MoreVertical,
  Calendar,
  User,
  Tag
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/hooks/use-toast'

interface MediaAsset {
  id: string
  filename: string
  original_filename: string
  media_type: 'image' | 'video' | 'document'
  file_size: number
  url: string
  thumbnail_url?: string
  created_at: string
  tags: string[]
  dimensions?: { width: number; height: number }
  duration?: number
}

// Real media assets will be loaded from the database
// Empty state until media upload and storage is implemented

export default function MediaLibraryPage() {
  const [assets, setAssets] = useState<MediaAsset[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<'all' | 'image' | 'video' | 'document'>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [isUploading, setIsUploading] = useState(false)
  const { toast } = useToast()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsUploading(true)

    try {
      // Mock upload - replace with real API call
      for (const file of acceptedFiles) {
        await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate upload

        const newAsset: MediaAsset = {
          id: Date.now().toString(),
          filename: file.name.toLowerCase().replace(/\s+/g, '-'),
          original_filename: file.name,
          media_type: file.type.startsWith('image/') ? 'image' :
                     file.type.startsWith('video/') ? 'video' : 'document',
          file_size: file.size,
          url: URL.createObjectURL(file),
          created_at: new Date().toISOString(),
          tags: []
        }

        setAssets(prev => [newAsset, ...prev])
      }

      toast({
        title: "Upload successful",
        description: `${acceptedFiles.length} file(s) uploaded successfully.`,
      })
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "There was an error uploading your files.",
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
    }
  }, [toast])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'video/*': ['.mp4', '.mov', '.avi', '.mkv'],
      'application/pdf': ['.pdf'],
      'text/*': ['.txt', '.md']
    },
    maxSize: 50 * 1024 * 1024 // 50MB
  })

  const filteredAssets = assets.filter(asset => {
    const matchesSearch = asset.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         asset.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesType = selectedType === 'all' || asset.media_type === selectedType
    return matchesSearch && matchesType
  })

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getMediaIcon = (type: string) => {
    switch (type) {
      case 'image': return <ImageIcon className="h-4 w-4" />
      case 'video': return <Video className="h-4 w-4" />
      default: return <FileText className="h-4 w-4" />
    }
  }

  const copyToClipboard = (url: string) => {
    navigator.clipboard.writeText(url)
    toast({
      title: "URL copied",
      description: "Media URL copied to clipboard.",
    })
  }

  const deleteAsset = (id: string) => {
    setAssets(prev => prev.filter(asset => asset.id !== id))
    toast({
      title: "Asset deleted",
      description: "Media asset has been deleted.",
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Media Library</h1>
          <p className="text-muted-foreground">
            Manage your images, videos, and documents
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            {viewMode === 'grid' ? <List className="h-4 w-4" /> : <Grid3X3 className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Upload Area */}
      <Card>
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {isDragActive ? 'Drop files here' : 'Upload media files'}
            </h3>
            <p className="text-muted-foreground mb-4">
              Drag and drop files here, or click to select files
            </p>
            <p className="text-sm text-muted-foreground">
              Supports images, videos, and documents up to 50MB
            </p>
            {isUploading && (
              <div className="mt-4">
                <div className="animate-pulse text-primary">Uploading...</div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search media files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Tabs value={selectedType} onValueChange={(value) => setSelectedType(value as 'all' | 'image' | 'video' | 'document')}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="image">Images</TabsTrigger>
            <TabsTrigger value="video">Videos</TabsTrigger>
            <TabsTrigger value="document">Documents</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Media Grid/List */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredAssets.map((asset) => (
            <Card key={asset.id} className="group hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="aspect-square bg-muted rounded-lg mb-3 relative overflow-hidden">
                  {asset.media_type === 'image' ? (
                    <img
                      src={asset.thumbnail_url || asset.url}
                      alt={asset.original_filename}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      {getMediaIcon(asset.media_type)}
                    </div>
                  )}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="secondary" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => window.open(asset.url, '_blank')}>
                          <Eye className="mr-2 h-4 w-4" />
                          View
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => copyToClipboard(asset.url)}>
                          <Copy className="mr-2 h-4 w-4" />
                          Copy URL
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="mr-2 h-4 w-4" />
                          Download
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => deleteAsset(asset.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="font-medium text-sm truncate" title={asset.original_filename}>
                    {asset.original_filename}
                  </h3>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{formatFileSize(asset.file_size)}</span>
                    {asset.duration && <span>{formatDuration(asset.duration)}</span>}
                    {asset.dimensions && (
                      <span>{asset.dimensions.width}×{asset.dimensions.height}</span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {asset.tags.slice(0, 2).map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {asset.tags.length > 2 && (
                      <Badge variant="outline" className="text-xs">
                        +{asset.tags.length - 2}
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {filteredAssets.map((asset) => (
                <div key={asset.id} className="flex items-center p-4 hover:bg-muted/50">
                  <div className="flex items-center space-x-3 flex-1">
                    <div className="w-10 h-10 bg-muted rounded flex items-center justify-center">
                      {getMediaIcon(asset.media_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium truncate">{asset.original_filename}</h3>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>{formatFileSize(asset.file_size)}</span>
                        {asset.dimensions && (
                          <span>{asset.dimensions.width}×{asset.dimensions.height}</span>
                        )}
                        {asset.duration && <span>{formatDuration(asset.duration)}</span>}
                        <span>{new Date(asset.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex flex-wrap gap-1">
                      {asset.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => window.open(asset.url, '_blank')}>
                          <Eye className="mr-2 h-4 w-4" />
                          View
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => copyToClipboard(asset.url)}>
                          <Copy className="mr-2 h-4 w-4" />
                          Copy URL
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="mr-2 h-4 w-4" />
                          Download
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => deleteAsset(asset.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {filteredAssets.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No media files found</h3>
            <p className="text-muted-foreground">
              {searchTerm || selectedType !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Upload your first media file to get started'
              }
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
