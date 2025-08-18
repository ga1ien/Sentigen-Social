"use client"

import { useEffect, useState } from "react"
import { GlassCard, GlassCardContent, GlassCardDescription, GlassCardHeader, GlassCardTitle } from "@/components/zyyn/glass-card"
import { TrendingUp, Users, FileText, Activity, Zap, Target, Calendar, BarChart3 } from "lucide-react"
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs"

export default function DashboardPage() {
  const [userName, setUserName] = useState("")
  const supabase = createClientComponentClient()

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
        // Extract name from email or use metadata
        const name = user.user_metadata?.name || user.email?.split('@')[0] || 'there'
        setUserName(name)
      }
    }
    getUser()
  }, [])
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
              <TrendingUp className="w-4 h-4 text-green-400" />
            </div>
          </GlassCardHeader>
          <GlassCardContent>
            <div className="space-y-1">
              <p className="text-3xl font-light text-white">2.4M</p>
              <p className="text-xs text-green-400">+12% from last week</p>
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
              <p className="text-3xl font-light text-white">8.7%</p>
              <p className="text-xs text-blue-400">+3.2% from last week</p>
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
              <p className="text-3xl font-light text-white">1,842</p>
              <p className="text-xs text-purple-400">+24% from last week</p>
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
              <p className="text-3xl font-light text-white">47</p>
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
                {[
                  { title: "AI trends in 2025", platform: "linkedin", engagement: "12.4K", trend: "up" },
                  { title: "productivity tips thread", platform: "twitter", engagement: "8.2K", trend: "up" },
                  { title: "behind the scenes", platform: "instagram", engagement: "24.1K", trend: "down" },
                  { title: "weekly newsletter", platform: "email", engagement: "4.8K", trend: "up" },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all">
                    <div className="space-y-1">
                      <p className="text-sm text-white">{item.title}</p>
                      <p className="text-xs text-white/70">{item.platform}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-white/85">{item.engagement}</span>
                      {item.trend === "up" ? (
                        <TrendingUp className="w-4 h-4 text-green-400" />
                      ) : (
                        <TrendingUp className="w-4 h-4 text-red-400 rotate-180" />
                      )}
                    </div>
                  </div>
                ))}
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
                <button className="flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all">
                  <Zap className="w-5 h-5 mb-2 text-yellow-400" />
                  <span className="text-xs text-white/85">generate</span>
                </button>
                <button className="flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all">
                  <Calendar className="w-5 h-5 mb-2 text-blue-400" />
                  <span className="text-xs text-white/85">schedule</span>
                </button>
                <button className="flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all">
                  <BarChart3 className="w-5 h-5 mb-2 text-green-400" />
                  <span className="text-xs text-white/85">analyze</span>
                </button>
                <button className="flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all">
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
                <div className="p-3 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-white/10">
                  <p className="text-xs text-white mb-1">trending topic</p>
                  <p className="text-sm text-white/85">AI automation tools are gaining traction. Create content about workflow optimization.</p>
                </div>
                <div className="p-3 rounded-xl bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-white/10">
                  <p className="text-xs text-white mb-1">best time to post</p>
                  <p className="text-sm text-white/85">Your audience is most active at 2PM EST today.</p>
                </div>
                <div className="p-3 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-white/10">
                  <p className="text-xs text-white mb-1">content idea</p>
                  <p className="text-sm text-white/85">Share your morning routine for maximum productivity.</p>
                </div>
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
                {[
                  { day: "monday", posts: 3 },
                  { day: "tuesday", posts: 2 },
                  { day: "wednesday", posts: 4 },
                  { day: "thursday", posts: 2 },
                  { day: "friday", posts: 5 },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-white/85">{item.day}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-white/70">{item.posts} posts</span>
                      <div className="w-2 h-2 rounded-full bg-green-400/60" />
                    </div>
                  </div>
                ))}
              </div>
            </GlassCardContent>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}
