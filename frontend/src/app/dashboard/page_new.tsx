"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { useUser } from "@/contexts/user-context"
import { apiClient } from "@/lib/api"
import {
  PenTool,
  Calendar,
  BarChart3,
  TrendingUp,
  Users,
  Eye,
  Heart,
  MessageCircle,
  Share,
  Plus,
} from "lucide-react"

interface DashboardStats {
  totalPosts: number
  scheduledPosts: number
  engagement: number
  followers: number
}

interface RecentPost {
  id: string
  title: string
  platform: string
  time: string
  engagement: {
    views: number
    likes: number
    comments: number
    shares: number
  }
  status: string
}

export default function DashboardPage() {
  const { user, loading } = useUser()
  const [stats, setStats] = useState<DashboardStats>({
    totalPosts: 0,
    scheduledPosts: 0,
    engagement: 0,
    followers: 0
  })
  const [recentPosts, setRecentPosts] = useState<RecentPost[]>([])
  const [loadingData, setLoadingData] = useState(true)

  useEffect(() => {
    if (user && !loading) {
      loadDashboardData()
    }
  }, [user, loading])

  const loadDashboardData = async () => {
    try {
      setLoadingData(true)

      // Load user's posts and calculate stats
      // For now, we'll show empty state until backend integration is complete
      setStats({
        totalPosts: 0,
        scheduledPosts: 0,
        engagement: 0,
        followers: 0
      })
      setRecentPosts([])

    } catch (error) {
      console.error('Error loading dashboard data:', error)
    } finally {
      setLoadingData(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground">Loading your data...</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                <div className="h-4 w-4 bg-muted animate-pulse rounded" />
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
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground">Please log in to view your dashboard.</p>
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
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user.user_metadata?.full_name || user.email?.split('@')[0]}! Here&apos;s what&apos;s happening with your social media.
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Create Post
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Posts</CardTitle>
            <PenTool className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loadingData ? "..." : stats.totalPosts}</div>
            <p className="text-xs text-muted-foreground">
              {stats.totalPosts === 0 ? "Start creating content!" : "Your published posts"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loadingData ? "..." : stats.scheduledPosts}</div>
            <p className="text-xs text-muted-foreground">
              {stats.scheduledPosts === 0 ? "No scheduled posts" : "Ready to publish"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Engagement</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loadingData ? "..." : `${stats.engagement}%`}</div>
            <p className="text-xs text-muted-foreground">
              {stats.engagement === 0 ? "Connect social accounts" : "Average engagement rate"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Followers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loadingData ? "..." : stats.followers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {stats.followers === 0 ? "Connect social accounts" : "Total followers"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Your latest posts and their performance</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentPosts.length === 0 ? (
              <div className="text-center py-8">
                <PenTool className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No posts yet</h3>
                <p className="text-muted-foreground mb-4">
                  Start creating content to see your activity here.
                </p>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Post
                </Button>
              </div>
            ) : (
              recentPosts.map((post, index) => (
                <div key={index} className="flex items-center space-x-4 p-4 border rounded-lg">
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium leading-none">{post.title}</p>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary">{post.platform}</Badge>
                      <Badge variant={post.status === "published" ? "default" : "outline"}>
                        {post.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{post.time}</span>
                    </div>
                  </div>
                  <div className="flex space-x-4 text-sm text-muted-foreground">
                    <div className="flex items-center">
                      <Eye className="mr-1 h-3 w-3" />
                      {post.engagement.views}
                    </div>
                    <div className="flex items-center">
                      <Heart className="mr-1 h-3 w-3" />
                      {post.engagement.likes}
                    </div>
                    <div className="flex items-center">
                      <MessageCircle className="mr-1 h-3 w-3" />
                      {post.engagement.comments}
                    </div>
                    <div className="flex items-center">
                      <Share className="mr-1 h-3 w-3" />
                      {post.engagement.shares}
                    </div>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* This Week */}
        <Card>
          <CardHeader>
            <CardTitle>This Week</CardTitle>
            <CardDescription>Your performance summary</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Posts Published</span>
                <span className="text-sm text-muted-foreground">0 / 10</span>
              </div>
              <Progress value={0} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Engagement Goal</span>
                <span className="text-sm text-muted-foreground">0% / 8%</span>
              </div>
              <Progress value={0} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Follower Growth</span>
                <span className="text-sm text-muted-foreground">0 / 200</span>
              </div>
              <Progress value={0} className="h-2" />
            </div>

            <div className="pt-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Top Performing Platform</span>
                <Badge variant="outline">Connect accounts</Badge>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Best Posting Time</span>
                <span className="text-sm text-muted-foreground">No data yet</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Get started with common tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" className="h-24 flex-col space-y-2">
              <PenTool className="h-6 w-6" />
              <span>Create Post</span>
            </Button>
            <Button variant="outline" className="h-24 flex-col space-y-2">
              <Calendar className="h-6 w-6" />
              <span>Schedule Content</span>
            </Button>
            <Button variant="outline" className="h-24 flex-col space-y-2">
              <BarChart3 className="h-6 w-6" />
              <span>View Analytics</span>
            </Button>
            <Button variant="outline" className="h-24 flex-col space-y-2">
              <Users className="h-6 w-6" />
              <span>Manage Team</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
