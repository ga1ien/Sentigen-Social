"use client"

import { useEffect, useState } from "react"
import { GlassCard, GlassCardContent, GlassCardDescription, GlassCardHeader, GlassCardTitle } from "@/components/zyyn/glass-card"
import { TrendingUp, Users, FileText, Activity, Zap, Target, Calendar, BarChart3, Loader2 } from "lucide-react"
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs"
import { useToast } from "@/hooks/use-toast"

interface Stats {
  totalReach: number
  reachChange: number
  engagement: number
  engagementChange: number
  newFollowers: number
  followersChange: number
  contentCreated: number
}

interface Post {
  id: string
  content: string
  platform: string
  engagement_count: number
  created_at: string
  status: string
}

interface Suggestion {
  id: string
  type: string
  title: string
  description: string
}

interface ScheduledPost {
  date: string
  count: number
}

export default function DashboardPage() {
  const [userName, setUserName] = useState("")
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Stats>({
    totalReach: 0,
    reachChange: 0,
    engagement: 0,
    engagementChange: 0,
    newFollowers: 0,
    followersChange: 0,
    contentCreated: 0
  })
  const [recentPosts, setRecentPosts] = useState<Post[]>([])
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [upcomingPosts, setUpcomingPosts] = useState<ScheduledPost[]>([])

  const supabase = createClientComponentClient()
  const { toast } = useToast()

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)

      // Get user data
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
        const name = user.user_metadata?.name || user.email?.split('@')[0] || 'there'
        setUserName(name)
      }

      // Fetch analytics stats
      const { data: analyticsData } = await supabase
        .from('analytics')
        .select('*')
        .eq('user_id', user?.id)
        .order('created_at', { ascending: false })
        .limit(1)
        .single()

      if (analyticsData) {
        setStats({
          totalReach: analyticsData.total_reach || 0,
          reachChange: analyticsData.reach_change || 0,
          engagement: analyticsData.engagement_rate || 0,
          engagementChange: analyticsData.engagement_change || 0,
          newFollowers: analyticsData.new_followers || 0,
          followersChange: analyticsData.followers_change || 0,
          contentCreated: analyticsData.content_count || 0
        })
      }

      // Fetch recent posts
      const { data: postsData } = await supabase
        .from('social_media_posts')
        .select('*')
        .eq('user_id', user?.id)
        .order('created_at', { ascending: false })
        .limit(4)

      if (postsData) {
        setRecentPosts(postsData)
      }

      // Fetch AI suggestions
      const { data: suggestionsData } = await supabase
        .from('ai_suggestions')
        .select('*')
        .eq('user_id', user?.id)
        .eq('is_active', true)
        .order('created_at', { ascending: false })
        .limit(3)

      if (suggestionsData) {
        setSuggestions(suggestionsData)
      }

      // Fetch upcoming scheduled posts
      const { data: scheduledData } = await supabase
        .from('scheduled_posts')
        .select('scheduled_time')
        .eq('user_id', user?.id)
        .eq('status', 'pending')
        .gte('scheduled_time', new Date().toISOString())
        .order('scheduled_time', { ascending: true })

      if (scheduledData) {
        // Group by day
        const grouped = scheduledData.reduce((acc: any, post: any) => {
          const date = new Date(post.scheduled_time).toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase()
          acc[date] = (acc[date] || 0) + 1
          return acc
        }, {})

        const upcoming = Object.entries(grouped).map(([date, count]) => ({
          date,
          count: count as number
        })).slice(0, 5)

        setUpcomingPosts(upcoming)
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      toast({
        title: "Error loading dashboard",
        description: "Some data may not be available",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const formatChange = (change: number) => {
    const sign = change >= 0 ? '+' : ''
    return `${sign}${change}%`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-white/60" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-light text-white">welcome back{userName && `, ${userName}`}</h1>
        <p className="text-white/80">here's what's happening with your content today</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassCard variant="elevated" glow>
          <GlassCardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <GlassCardTitle className="text-base font-normal">total reach</GlassCardTitle>
              <TrendingUp className={`w-4 h-4 ${stats.reachChange >= 0 ? 'text-green-400' : 'text-red-400 rotate-180'}`} />
            </div>
          </GlassCardHeader>
          <GlassCardContent>
            <div className="space-y-1">
              <p className="text-3xl font-light text-white">{formatNumber(stats.totalReach)}</p>
              <p className={`text-xs ${stats.reachChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {formatChange(stats.reachChange)} from last week
              </p>
            </div>
          </GlassCardContent>
        </GlassCard>

        <GlassCard variant="elevated" glow>
          <GlassCardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <GlassCardTitle className="text-base font-normal">engagement</GlassCardTitle>
              <Activity className="w-4 h-4 text-blue-400" />
            </div>
          </GlassCardHeader>
          <GlassCardContent>
            <div className="space-y-1">
              <p className="text-3xl font-light text-white">{stats.engagement.toFixed(1)}%</p>
              <p className={`text-xs ${stats.engagementChange >= 0 ? 'text-blue-400' : 'text-red-400'}`}>
                {formatChange(stats.engagementChange)} from last week
              </p>
            </div>
          </GlassCardContent>
        </GlassCard>

        <GlassCard variant="elevated" glow>
          <GlassCardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <GlassCardTitle className="text-base font-normal">new followers</GlassCardTitle>
              <Users className="w-4 h-4 text-purple-400" />
            </div>
          </GlassCardHeader>
          <GlassCardContent>
            <div className="space-y-1">
              <p className="text-3xl font-light text-white">{formatNumber(stats.newFollowers)}</p>
              <p className={`text-xs ${stats.followersChange >= 0 ? 'text-purple-400' : 'text-red-400'}`}>
                {formatChange(stats.followersChange)} from last week
              </p>
            </div>
          </GlassCardContent>
        </GlassCard>

        <GlassCard variant="elevated" glow>
          <GlassCardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <GlassCardTitle className="text-base font-normal">content created</GlassCardTitle>
              <FileText className="w-4 h-4 text-orange-400" />
            </div>
          </GlassCardHeader>
          <GlassCardContent>
            <div className="space-y-1">
              <p className="text-3xl font-light text-white">{stats.contentCreated}</p>
              <p className="text-xs text-orange-400">this week</p>
            </div>
          </GlassCardContent>
        </GlassCard>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 space-y-4">
          <GlassCard variant="default" blur="lg">
            <GlassCardHeader>
              <GlassCardTitle>recent activity</GlassCardTitle>
              <GlassCardDescription>your latest content performance</GlassCardDescription>
            </GlassCardHeader>
            <GlassCardContent>
              <div className="space-y-4">
                {recentPosts.length > 0 ? (
                  recentPosts.map((post) => (
                    <div key={post.id} className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all">
                      <div className="space-y-1">
                        <p className="text-sm text-white truncate max-w-[300px]">
                          {post.content || 'Untitled post'}
                        </p>
                        <p className="text-xs text-white/70">{post.platform || 'multiple'}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-white/85">
                          {formatNumber(post.engagement_count || 0)}
                        </span>
                        {post.status === 'published' ? (
                          <div className="w-2 h-2 rounded-full bg-green-400" />
                        ) : (
                          <div className="w-2 h-2 rounded-full bg-yellow-400" />
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-white/60 py-8">No recent posts yet</p>
                )}
              </div>
            </GlassCardContent>
          </GlassCard>

          {/* Quick Actions */}
          <GlassCard variant="subtle" blur="lg">
            <GlassCardHeader>
              <GlassCardTitle>quick actions</GlassCardTitle>
            </GlassCardHeader>
            <GlassCardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <button
                  onClick={() => window.location.href = '/dashboard/create'}
                  className="flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                >
                  <Zap className="w-5 h-5 mb-2 text-yellow-400" />
                  <span className="text-xs text-white/85">generate</span>
                </button>
                <button
                  onClick={() => window.location.href = '/dashboard/calendar'}
                  className="flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                >
                  <Calendar className="w-5 h-5 mb-2 text-blue-400" />
                  <span className="text-xs text-white/85">schedule</span>
                </button>
                <button
                  onClick={() => window.location.href = '/dashboard/analytics'}
                  className="flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                >
                  <BarChart3 className="w-5 h-5 mb-2 text-green-400" />
                  <span className="text-xs text-white/85">analyze</span>
                </button>
                <button
                  onClick={() => window.location.href = '/dashboard/intelligence'}
                  className="flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                >
                  <Target className="w-5 h-5 mb-2 text-purple-400" />
                  <span className="text-xs text-white/85">optimize</span>
                </button>
              </div>
            </GlassCardContent>
          </GlassCard>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* AI Suggestions */}
          <GlassCard variant="elevated" blur="lg" glow>
            <GlassCardHeader>
              <GlassCardTitle>ai suggestions</GlassCardTitle>
              <GlassCardDescription>personalized for you</GlassCardDescription>
            </GlassCardHeader>
            <GlassCardContent>
              <div className="space-y-3">
                {suggestions.length > 0 ? (
                  suggestions.map((suggestion) => (
                    <div key={suggestion.id} className="p-3 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-white/10">
                      <p className="text-xs text-white mb-1">{suggestion.type}</p>
                      <p className="text-sm text-white/85">{suggestion.description}</p>
                    </div>
                  ))
                ) : (
                  <div className="space-y-3">
                    <div className="p-3 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-white/10">
                      <p className="text-xs text-white mb-1">getting started</p>
                      <p className="text-sm text-white/85">Create your first post to start getting personalized suggestions</p>
                    </div>
                  </div>
                )}
              </div>
            </GlassCardContent>
          </GlassCard>

          {/* Upcoming */}
          <GlassCard variant="default" blur="lg">
            <GlassCardHeader>
              <GlassCardTitle>upcoming</GlassCardTitle>
              <GlassCardDescription>next 7 days</GlassCardDescription>
            </GlassCardHeader>
            <GlassCardContent>
              <div className="space-y-3">
                {upcomingPosts.length > 0 ? (
                  upcomingPosts.map((item, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm text-white/85">{item.date}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-white/70">{item.count} posts</span>
                        <div className="w-2 h-2 rounded-full bg-green-400/60" />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-white/60 py-4">No scheduled posts</p>
                )}
              </div>
            </GlassCardContent>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}
