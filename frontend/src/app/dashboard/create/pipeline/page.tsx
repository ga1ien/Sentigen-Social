"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { toast } from "@/lib/toast-filter"
import { RichTextEditor } from "@/components/editor/rich-text-editor"
import {
  CheckCircle,
  Clock,
  FileText,
  Linkedin,
  Play,
  Video,
  Wand2,
  Youtube,
  Instagram,
} from "lucide-react"
import { apiClient } from "@/lib/api"

type OutputType = "script" | "linkedin_post"

interface StartedResearch {
  id: string
  status: string
  source: string
  query: string
  created_at: string
}

interface ResearchResult {
  id: string
  status: string
  source: string
  query: string
  results_count: number
  insights: Record<string, any>
  raw_data: any[]
  created_at: string
  completed_at?: string
}

export default function ResearchToContentPipelinePage() {
  // Using filtered toast that only shows warnings/errors

  // Step state
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1)

  // Step 1: choose output type
  const [outputType, setOutputType] = useState<OutputType>("linkedin_post")

  // Step 2: topic & research
  const [topic, setTopic] = useState("")
  const [source, setSource] = useState("reddit")
  const [analysisDepth, setAnalysisDepth] = useState("standard")
  const [maxItems, setMaxItems] = useState(10)
  const [isStartingResearch, setIsStartingResearch] = useState(false)
  const [researchSessionId, setResearchSessionId] = useState<string | null>(null)
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Step 3: synthesize & edit
  const [tone, setTone] = useState("professional")
  const [length, setLength] = useState("medium")
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedTitle, setGeneratedTitle] = useState("")
  const [content, setContent] = useState("")
  const [isSavingDraft, setIsSavingDraft] = useState(false)

  // Step 4A: LinkedIn publish/schedule
  const [scheduleDate, setScheduleDate] = useState("")
  const [isPostingNow, setIsPostingNow] = useState(false)
  const [isScheduling, setIsScheduling] = useState(false)
  const [isAutoScheduling, setIsAutoScheduling] = useState(false)

  // Step 4B: Script -> Video via HeyGen
  const [isCreatingVideo, setIsCreatingVideo] = useState(false)
  const [videoJobId, setVideoJobId] = useState<string | null>(null)
  const [videoStatus, setVideoStatus] = useState<any | null>(null)
  const videoPollRef = useRef<NodeJS.Timeout | null>(null)
  const [shortPlatforms, setShortPlatforms] = useState<string[]>(["youtube", "instagram"]) // backend supports these two
  const [isPostingShorts, setIsPostingShorts] = useState(false)

  const desiredContentType = useMemo(() => {
    return outputType === "linkedin_post" ? "post" : "article"
  }, [outputType])

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
      if (videoPollRef.current) clearInterval(videoPollRef.current)
    }
  }, [])

  const startResearch = async () => {
    if (!topic.trim()) {
      toast({ title: "Topic required", description: "Please enter a topic to research.", variant: "destructive" })
      return
    }
    setIsStartingResearch(true)
    setResearchResult(null)
    try {
      const res = await apiClient.startResearch({
        query: topic,
        source: source as any,
        max_items: maxItems,
        analysis_depth: analysisDepth as any,
      })
      const data = res.data as StartedResearch
      setResearchSessionId(data.id)
      setStep(2)

      // poll status until completed
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = setInterval(async () => {
        try {
          if (!data.id) return
          const s = await apiClient.getResearchSession(data.id)
          const rr = s.data as ResearchResult
          if (rr.status === "completed" || rr.status === "failed") {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
            setResearchResult(rr)
            if (rr.status === "completed") {
              // Success - no toast notification
              setStep(3)
            } else {
              toast({ title: "Research failed", description: "Please try again.", variant: "destructive" })
            }
          }
        } catch (e) {
          // ignore transient errors
        }
      }, 3000)
    } catch (e: any) {
      if (e?.response?.status === 401) {
        toast({ title: "sign in required", description: "please sign in to start research", variant: "destructive" })
        return
      }
      toast({ title: "Failed to start research", description: e?.response?.data?.detail || String(e), variant: "destructive" })
    } finally {
      setIsStartingResearch(false)
    }
  }

  const generateFromResearch = async () => {
    if (!researchSessionId) return
    setIsGenerating(true)
    try {
      const res = await apiClient.generateFromResearch({
        research_session_id: researchSessionId,
        content_type: desiredContentType as any,
        platform: outputType === "linkedin_post" ? "linkedin" : undefined,
        tone,
        length: length as any,
      })
      const data = res.data
      setGeneratedTitle(data.title || "")
      setContent(data.content || "")
      // Success - no toast notification
    } catch (e: any) {
      if (e?.response?.status === 401) {
        toast({ title: "sign in required", description: "please sign in to generate content", variant: "destructive" })
        return
      }
      toast({ title: "Generation failed", description: e?.response?.data?.detail || String(e), variant: "destructive" })
    } finally {
      setIsGenerating(false)
    }
  }

  const saveDraft = async () => {
    if (!content.trim()) {
      toast({ title: "Nothing to save", description: "Please generate or write content first.", variant: "destructive" })
      return
    }
    setIsSavingDraft(true)
    try {
      const res = await apiClient.saveDraft({ platform: outputType === "linkedin_post" ? "linkedin" : undefined, title: generatedTitle, content })
      // Success - draft saved
    } catch (e: any) {
      if (e?.response?.status === 401) {
        toast({ title: "sign in required", description: "please sign in to save drafts", variant: "destructive" })
        return
      }
      toast({ title: "Save failed", description: e?.response?.data?.detail || String(e), variant: "destructive" })
    } finally {
      setIsSavingDraft(false)
    }
  }

  const postNowLinkedIn = async () => {
    if (!content.trim()) {
      toast({ title: "Content required", description: "Add or generate content first.", variant: "destructive" })
      return
    }
    setIsPostingNow(true)
    try {
      await apiClient.socialPostingCreate({ content, platforms: ["linkedin"] })
      // Success - posted to LinkedIn
    } catch (e: any) {
      if (e?.response?.status === 401) {
        toast({ title: "sign in required", description: "please sign in to publish", variant: "destructive" })
        return
      }
      toast({ title: "Publish failed", description: e?.response?.data?.detail || String(e), variant: "destructive" })
    } finally {
      setIsPostingNow(false)
    }
  }

  const scheduleLinkedIn = async () => {
    if (!content.trim() || !scheduleDate) {
      toast({ title: "Schedule info missing", description: "Set content and a datetime.", variant: "destructive" })
      return
    }
    setIsScheduling(true)
    try {
      await apiClient.socialPostingCreate({ content, platforms: ["linkedin"], schedule_date: new Date(scheduleDate).toISOString() })
      // Success - scheduled for posting
    } catch (e: any) {
      if (e?.response?.status === 401) {
        toast({ title: "sign in required", description: "please sign in to schedule", variant: "destructive" })
        return
      }
      toast({ title: "Schedule failed", description: e?.response?.data?.detail || String(e), variant: "destructive" })
    } finally {
      setIsScheduling(false)
    }
  }

  const autoScheduleLinkedIn = async () => {
    if (!content.trim()) {
      toast({ title: "Content required", description: "Add or generate content first.", variant: "destructive" })
      return
    }
    setIsAutoScheduling(true)
    try {
      await apiClient.socialPostingCreate({ content, platforms: ["linkedin"], auto_schedule: { schedule: true, title: "default" } })
      // Success - added to auto schedule
    } catch (e: any) {
      if (e?.response?.status === 401) {
        toast({ title: "sign in required", description: "please sign in to auto schedule", variant: "destructive" })
        return
      }
      toast({ title: "Auto schedule failed", description: e?.response?.data?.detail || String(e), variant: "destructive" })
    } finally {
      setIsAutoScheduling(false)
    }
  }

  const createVideo = async () => {
    if (!content.trim()) {
      toast({ title: "Script required", description: "Generate or write your script first.", variant: "destructive" })
      return
    }
    setIsCreatingVideo(true)
    try {
      const res = await apiClient.generateHeyGenVideo({ script: content })
      const id = res.data?.id || res.data?.videoId || res.data?.video_id || res.data?.data?.id
      if (!id) throw new Error("No video id returned")
      setVideoJobId(id)
      setStep(4)
      if (videoPollRef.current) clearInterval(videoPollRef.current)
      videoPollRef.current = setInterval(async () => {
        try {
          const s = await apiClient.getHeyGenVideo(id)
          setVideoStatus(s.data)
          const status = s.data?.status || s.data?.data?.status
          if (status && ["completed", "ready", "failed"].includes(String(status).toLowerCase())) {
            if (videoPollRef.current) clearInterval(videoPollRef.current)
            if (String(status).toLowerCase() === "failed") {
              toast({ title: "Video failed", description: "Please try again.", variant: "destructive" })
            } else {
              // Success - video ready
            }
          }
        } catch {
          // ignore
        }
      }, 4000)
    } catch (e: any) {
      if (e?.response?.status === 401) {
        toast({ title: "sign in required", description: "please sign in to create video", variant: "destructive" })
        return
      }
      toast({ title: "Video start failed", description: e?.response?.data?.detail || String(e), variant: "destructive" })
    } finally {
      setIsCreatingVideo(false)
    }
  }

  const postShorts = async () => {
    const videoUrl = videoStatus?.video_url || videoStatus?.data?.videoUrl || videoStatus?.data?.video_url
    if (!videoUrl) {
      toast({ title: "No video URL", description: "Wait until the video is ready.", variant: "destructive" })
      return
    }
    setIsPostingShorts(true)
    try {
      await apiClient.socialPostingCreate({
        content: generatedTitle || "New short",
        platforms: shortPlatforms,
        media_urls: [videoUrl],
      })
      // Success - published to shorts platforms
    } catch (e: any) {
      if (e?.response?.status === 401) {
        toast({ title: "sign in required", description: "please sign in to publish", variant: "destructive" })
        return
      }
      toast({ title: "Publish failed", description: e?.response?.data?.detail || String(e), variant: "destructive" })
    } finally {
      setIsPostingShorts(false)
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Research → Content Pipeline</h1>
        <p className="text-muted-foreground">Research a topic, synthesize content, edit, and publish/schedule. Or create a video from your script.</p>
      </div>

      <Tabs value={String(step)}>
        <TabsList className="grid grid-cols-4 w-full">
          <TabsTrigger value="1">Choose Output</TabsTrigger>
          <TabsTrigger value="2">Research</TabsTrigger>
          <TabsTrigger value="3">Synthesize & Edit</TabsTrigger>
          <TabsTrigger value="4">Publish</TabsTrigger>
        </TabsList>

        <TabsContent value="1" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Step 1: Choose Output</CardTitle>
              <CardDescription>Select whether you want a LinkedIn post or a script to turn into video.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <Button
                variant={outputType === "linkedin_post" ? "default" : "outline"}
                className="h-24 justify-start"
                onClick={() => setOutputType("linkedin_post")}
              >
                <Linkedin className="mr-2 h-5 w-5" /> LinkedIn post
              </Button>
              <Button
                variant={outputType === "script" ? "default" : "outline"}
                className="h-24 justify-start"
                onClick={() => setOutputType("script")}
              >
                <FileText className="mr-2 h-5 w-5" /> Script (to video)
              </Button>
            </CardContent>
          </Card>
          <div className="flex justify-end">
            <Button onClick={() => setStep(2)} disabled={!outputType}>Continue</Button>
          </div>
        </TabsContent>

        <TabsContent value="2" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Step 2: Topic & Research</CardTitle>
              <CardDescription>Start a research session and wait for completion.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Topic</Label>
                  <Input placeholder="e.g., AI automation tools" value={topic} onChange={(e) => setTopic(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Source</Label>
                  <Select value={source} onValueChange={setSource}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="reddit">Reddit</SelectItem>
                      <SelectItem value="hackernews">Hacker News</SelectItem>
                      <SelectItem value="github">GitHub</SelectItem>
                      <SelectItem value="google_trends">Google Trends</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Analysis depth</Label>
                  <Select value={analysisDepth} onValueChange={setAnalysisDepth}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quick">Quick</SelectItem>
                      <SelectItem value="standard">Standard</SelectItem>
                      <SelectItem value="comprehensive">Comprehensive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Max items</Label>
                  <Input type="number" min={1} max={50} value={maxItems} onChange={(e) => setMaxItems(parseInt(e.target.value || "10"))} />
                </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={startResearch} disabled={isStartingResearch}>
                  <Wand2 className="mr-2 h-4 w-4" /> {isStartingResearch ? "Starting..." : "Start Research"}
                </Button>
                {researchSessionId && (
                  <Badge variant="secondary">Session: {researchSessionId.slice(0, 8)}…</Badge>
                )}
              </div>

              {!researchResult && researchSessionId && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground"><Clock className="h-4 w-4 animate-spin" /> Research running...</div>
              )}

              {researchResult && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-green-600"><CheckCircle className="h-5 w-5" /> Research completed</div>
                  <div className="text-sm text-muted-foreground">Results: {researchResult.results_count}</div>
                </div>
              )}
            </CardContent>
          </Card>
          <div className="flex justify-end">
            <Button onClick={() => setStep(3)} disabled={!researchResult}>Continue</Button>
          </div>
        </TabsContent>

        <TabsContent value="3" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Step 3: Synthesize & Edit</CardTitle>
              <CardDescription>Generate AI content from your research and refine it.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Tone</Label>
                  <Select value={tone} onValueChange={setTone}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="casual">Casual</SelectItem>
                      <SelectItem value="engaging">Engaging</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Length</Label>
                  <Select value={length} onValueChange={setLength}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="short">Short</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="long">Long</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Content type</Label>
                  <Input value={desiredContentType} disabled />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={generateFromResearch} disabled={isGenerating || !researchResult}>
                  <Wand2 className="mr-2 h-4 w-4" /> {isGenerating ? "Generating..." : "Generate"}
                </Button>
                <Button variant="outline" onClick={saveDraft} disabled={isSavingDraft || !content.trim()}>Save Draft</Button>
              </div>
              <div className="space-y-2">
                <Label>Title</Label>
                <Input value={generatedTitle} onChange={(e) => setGeneratedTitle(e.target.value)} placeholder="Optional title" />
              </div>
              <RichTextEditor content={content} onChange={setContent} placeholder="Your content..." maxLength={5000} platforms={[outputType === "linkedin_post" ? "linkedin" : "article"]} />
            </CardContent>
          </Card>
          <div className="flex justify-end">
            <Button onClick={() => setStep(4)} disabled={!content.trim()}>Continue</Button>
          </div>
        </TabsContent>

        <TabsContent value="4" className="space-y-6">
          {outputType === "linkedin_post" ? (
            <Card>
              <CardHeader>
                <CardTitle>Step 4A: Publish LinkedIn</CardTitle>
                <CardDescription>Post now, schedule, or add to auto schedule.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Button onClick={postNowLinkedIn} disabled={isPostingNow}><Linkedin className="mr-2 h-4 w-4" /> {isPostingNow ? "Posting..." : "Post now"}</Button>
                  <Button variant="secondary" onClick={autoScheduleLinkedIn} disabled={isAutoScheduling}> {isAutoScheduling ? "Queuing..." : "Auto Schedule"}</Button>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Schedule date</Label>
                    <Input type="datetime-local" value={scheduleDate} onChange={(e) => setScheduleDate(e.target.value)} />
                  </div>
                </div>
                <Button variant="outline" onClick={scheduleLinkedIn} disabled={isScheduling || !scheduleDate}><Clock className="mr-2 h-4 w-4" /> {isScheduling ? "Scheduling..." : "Schedule"}</Button>
              </CardContent>
            </Card>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Step 4B: Create Video (HeyGen)</CardTitle>
                  <CardDescription>Generate an AI video from your script, then publish as shorts.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Button onClick={createVideo} disabled={isCreatingVideo}><Video className="mr-2 h-4 w-4" /> {isCreatingVideo ? "Starting..." : "Create video"}</Button>
                    {videoJobId && <Badge variant="secondary">Job: {videoJobId.slice(0, 8)}…</Badge>}
                  </div>
                  {videoStatus && (
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">Status: {String(videoStatus?.status || videoStatus?.data?.status)}</div>
                      {videoStatus?.video_url && (
                        <video src={videoStatus.video_url} controls className="w-full rounded border" />
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Publish Shorts</CardTitle>
                  <CardDescription>Select platforms and publish.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Button variant={shortPlatforms.includes("youtube") ? "default" : "outline"} onClick={() => setShortPlatforms((p) => p.includes("youtube") ? p.filter(x => x !== "youtube") : [...p, "youtube"]) }>
                      <Youtube className="mr-2 h-4 w-4" /> YouTube
                    </Button>
                    <Button variant={shortPlatforms.includes("instagram") ? "default" : "outline"} onClick={() => setShortPlatforms((p) => p.includes("instagram") ? p.filter(x => x !== "instagram") : [...p, "instagram"]) }>
                      <Instagram className="mr-2 h-4 w-4" /> Instagram
                    </Button>
                  </div>
                  <Button onClick={postShorts} disabled={isPostingShorts}><Play className="mr-2 h-4 w-4" /> {isPostingShorts ? "Publishing..." : "Publish"}</Button>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
