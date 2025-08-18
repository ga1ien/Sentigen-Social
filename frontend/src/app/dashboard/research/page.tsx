"use client"

import { useState } from "react"
import { GlassCard, GlassCardContent, GlassCardDescription, GlassCardHeader, GlassCardTitle } from "@/components/zyyn/glass-card"
import { Linkedin, Twitter, Instagram, Youtube, Music2, TrendingUp, Sparkles, Clock, Hash, Send } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

const platforms = [
  { id: "linkedin", name: "LinkedIn", icon: Linkedin, color: "blue" },
  { id: "twitter", name: "X", icon: Twitter, color: "gray" },
  { id: "instagram", name: "Instagram", icon: Instagram, color: "pink" },
  { id: "tiktok", name: "TikTok", icon: Music2, color: "purple" },
  { id: "youtube", name: "YouTube", icon: Youtube, color: "red" }
]

export default function ResearchPage() {
  const [selectedPlatform, setSelectedPlatform] = useState("linkedin")
  const [loading, setLoading] = useState(false)
  const [insights, setInsights] = useState<any>(null)
  const [draftContent, setDraftContent] = useState("")
  const { toast } = useToast()

  const fetchInsights = async (platform: string) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/research/platform-insights`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ platform })
      })
      const data = await response.json()
      setInsights(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch insights",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const generateDraft = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/research/draft-content`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          platform: selectedPlatform,
          topic: "AI and automation"
        })
      })
      const data = await response.json()
      setDraftContent(data.content)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate draft",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const selectedPlatformData = platforms.find(p => p.id === selectedPlatform)
  const Icon = selectedPlatformData?.icon || Linkedin

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-light text-white">content research</h1>
        <p className="text-white/80">discover insights and create platform-optimized content</p>
      </div>

      {/* Platform Selector - Large Glass Container */}
      <GlassCard variant="elevated" blur="xl" className="p-8">
        <div className="space-y-6">
          <h2 className="text-lg font-light text-white">select platform</h2>
          <div className="flex gap-4 flex-wrap">
            {platforms.map((platform) => {
              const PlatformIcon = platform.icon
              return (
                <button
                  key={platform.id}
                  onClick={() => {
                    setSelectedPlatform(platform.id)
                    fetchInsights(platform.id)
                  }}
                  className={`
                    flex flex-col items-center justify-center p-6 rounded-2xl
                    transition-all duration-300 min-w-[120px]
                    ${selectedPlatform === platform.id
                      ? 'bg-white/20 border-2 border-white/40 scale-105'
                      : 'bg-white/10 border border-white/20 hover:bg-white/15'}
                  `}
                >
                  <PlatformIcon className="w-8 h-8 mb-2 text-white" />
                  <span className="text-sm text-white">{platform.name}</span>
                </button>
              )
            })}
          </div>
        </div>
      </GlassCard>

      {/* Main Content Area - Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Left Column - Insights */}
        <GlassCard variant="elevated" blur="xl" className="p-8 min-h-[600px]">
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <Icon className="w-6 h-6 text-white" />
              <h2 className="text-xl font-light text-white">{selectedPlatformData?.name} insights</h2>
            </div>

            {/* Trending Topics */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-400" />
                <h3 className="text-sm font-medium text-white">trending now</h3>
              </div>
              <div className="space-y-2">
                {["AI automation tools", "Sustainable business", "Remote work culture"].map((topic, i) => (
                  <div key={i} className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer">
                    <p className="text-sm text-white/85">{topic}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Best Times */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-medium text-white">best times to post</h3>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {["Tuesday 9am", "Wednesday 2pm", "Thursday 10am", "Friday 3pm"].map((time, i) => (
                  <div key={i} className="p-2 rounded-lg bg-white/5 text-center">
                    <p className="text-xs text-white/85">{time}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Hashtags */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-medium text-white">recommended hashtags</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {["#AI", "#Innovation", "#TechTrends", "#FutureOfWork", "#Digital"].map((tag, i) => (
                  <span key={i} className="px-3 py-1 rounded-full bg-white/10 text-xs text-white/85 hover:bg-white/15 cursor-pointer">
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Content Tips */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-yellow-400" />
                <h3 className="text-sm font-medium text-white">platform tips</h3>
              </div>
              <ul className="space-y-2">
                <li className="text-sm text-white/80">• Use 3-5 hashtags for optimal reach</li>
                <li className="text-sm text-white/80">• Include a clear call-to-action</li>
                <li className="text-sm text-white/80">• Post during peak engagement hours</li>
                <li className="text-sm text-white/80">• Engage with comments quickly</li>
              </ul>
            </div>
          </div>
        </GlassCard>

        {/* Right Column - Content Creation */}
        <GlassCard variant="elevated" blur="xl" className="p-8 min-h-[600px]">
          <div className="space-y-6 h-full flex flex-col">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-light text-white">create content</h2>
              <button
                onClick={generateDraft}
                disabled={loading}
                className="px-4 py-2 rounded-xl bg-white/15 hover:bg-white/20 transition-all text-sm text-white flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                {loading ? "generating..." : "generate draft"}
              </button>
            </div>

            {/* Content Editor */}
            <div className="flex-1 space-y-4">
              <textarea
                value={draftContent}
                onChange={(e) => setDraftContent(e.target.value)}
                placeholder={`Write your ${selectedPlatformData?.name} content here...`}
                className="w-full h-[300px] p-4 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 resize-none"
              />

              {/* Character Count */}
              <div className="flex justify-between items-center">
                <span className="text-xs text-white/60">
                  {draftContent.length} characters
                </span>
                <span className="text-xs text-white/60">
                  optimal: {selectedPlatform === "twitter" ? "280" : selectedPlatform === "linkedin" ? "1500" : "150"}
                </span>
              </div>

              {/* Media Upload Area */}
              <div className="p-4 rounded-xl border-2 border-dashed border-white/20 text-center">
                <p className="text-sm text-white/60">drag media here or click to upload</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button className="flex-1 py-3 rounded-xl bg-white/10 hover:bg-white/15 transition-all text-white">
                save draft
              </button>
              <button className="flex-1 py-3 rounded-xl bg-white/20 hover:bg-white/25 transition-all text-white flex items-center justify-center gap-2">
                <Send className="w-4 h-4" />
                schedule post
              </button>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Content Ideas - Full Width Glass Container */}
      <GlassCard variant="elevated" blur="xl" className="p-8">
        <div className="space-y-6">
          <h2 className="text-xl font-light text-white">content ideas for {selectedPlatformData?.name}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer">
                <h3 className="text-sm font-medium text-white mb-2">Content Idea {i}</h3>
                <p className="text-xs text-white/70 mb-3">
                  Share your insights on the latest AI trends and how they're transforming your industry...
                </p>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-green-400">High engagement</span>
                  <button className="text-xs text-white/80 hover:text-white">use this →</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>
    </div>
  )
}
