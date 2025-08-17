"use client"

import { useState, useEffect } from 'react'
import { useUser } from '@/contexts/user-context'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
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
  TrendingUp,
  TrendingDown,
  Eye,
  Heart,
  MessageCircle,
  Share,
  Users,
  Calendar,
  Download,
  Filter,
  Twitter,
  Linkedin,
  Facebook,
  Instagram,
  Youtube
} from 'lucide-react'

// Mock data for analytics
const engagementData = [
  { date: '2024-08-01', views: 1200, likes: 89, comments: 23, shares: 12 },
  { date: '2024-08-02', views: 1450, likes: 102, comments: 31, shares: 18 },
  { date: '2024-08-03', views: 1100, likes: 76, comments: 19, shares: 8 },
  { date: '2024-08-04', views: 1800, likes: 134, comments: 42, shares: 25 },
  { date: '2024-08-05', views: 2100, likes: 156, comments: 38, shares: 31 },
  { date: '2024-08-06', views: 1650, likes: 98, comments: 27, shares: 15 },
  { date: '2024-08-07', views: 1900, likes: 142, comments: 35, shares: 22 },
]

const platformData = [
  { platform: 'LinkedIn', posts: 45, engagement: 8.2, followers: 5420, color: '#0077B5' },
  { platform: 'Twitter', posts: 78, engagement: 6.8, followers: 3210, color: '#1DA1F2' },
  { platform: 'Instagram', posts: 32, engagement: 12.4, followers: 8950, color: '#E4405F' },
  { platform: 'Facebook', posts: 28, engagement: 5.6, followers: 2180, color: '#1877F2' },
  { platform: 'YouTube', posts: 12, engagement: 15.2, followers: 1560, color: '#FF0000' },
]

const topPostsData = [
  {
    id: 1,
    title: "5 Productivity Tips That Changed My Life",
    platform: "LinkedIn",
    date: "2024-08-05",
    views: 2100,
    likes: 156,
    comments: 38,
    shares: 31,
    engagement: 10.7
  },
  {
    id: 2,
    title: "Behind the scenes of our latest project",
    platform: "Instagram",
    date: "2024-08-04",
    views: 1800,
    likes: 134,
    comments: 42,
    shares: 25,
    engagement: 11.2
  },
  {
    id: 3,
    title: "Quick tutorial: Setting up your workspace",
    platform: "YouTube",
    date: "2024-08-02",
    views: 1450,
    likes: 102,
    comments: 31,
    shares: 18,
    engagement: 10.4
  },
]

const audienceData = [
  { age: '18-24', percentage: 15, count: 1200 },
  { age: '25-34', percentage: 35, count: 2800 },
  { age: '35-44', percentage: 28, count: 2240 },
  { age: '45-54', percentage: 15, count: 1200 },
  { age: '55+', percentage: 7, count: 560 },
]

const platformIcons = {
  LinkedIn: Linkedin,
  Twitter: Twitter,
  Instagram: Instagram,
  Facebook: Facebook,
  YouTube: Youtube,
}

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('7d')
  const [selectedPlatform, setSelectedPlatform] = useState('all')

  const totalViews = engagementData.reduce((sum, item) => sum + item.views, 0)
  const totalLikes = engagementData.reduce((sum, item) => sum + item.likes, 0)
  const totalComments = engagementData.reduce((sum, item) => sum + item.comments, 0)
  const totalShares = engagementData.reduce((sum, item) => sum + item.shares, 0)
  const totalEngagement = ((totalLikes + totalComments + totalShares) / totalViews * 100).toFixed(1)

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Track your social media performance and engagement metrics
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalViews)}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                +12.5%
              </span>
              from last period
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Likes</CardTitle>
            <Heart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalLikes)}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                +8.2%
              </span>
              from last period
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Comments</CardTitle>
            <MessageCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalComments)}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                +15.3%
              </span>
              from last period
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Shares</CardTitle>
            <Share className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalShares)}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-red-600 flex items-center">
                <TrendingDown className="h-3 w-3 mr-1" />
                -2.1%
              </span>
              from last period
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Engagement Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalEngagement}%</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                +3.7%
              </span>
              from last period
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="platforms">Platforms</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="audience">Audience</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Engagement Trends */}
          <Card>
            <CardHeader>
              <CardTitle>Engagement Trends</CardTitle>
              <CardDescription>
                Track your engagement metrics over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={engagementData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="views"
                    stroke="#8884d8"
                    strokeWidth={2}
                    name="Views"
                  />
                  <Line
                    type="monotone"
                    dataKey="likes"
                    stroke="#82ca9d"
                    strokeWidth={2}
                    name="Likes"
                  />
                  <Line
                    type="monotone"
                    dataKey="comments"
                    stroke="#ffc658"
                    strokeWidth={2}
                    name="Comments"
                  />
                  <Line
                    type="monotone"
                    dataKey="shares"
                    stroke="#ff7300"
                    strokeWidth={2}
                    name="Shares"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Platform Performance */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Platform Distribution</CardTitle>
                <CardDescription>
                  Engagement by platform
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={platformData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="engagement"
                      label={({ platform, engagement }) => `${platform}: ${engagement}%`}
                    >
                      {platformData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Platform Comparison</CardTitle>
                <CardDescription>
                  Posts and engagement by platform
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={platformData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="platform" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="posts" fill="#8884d8" name="Posts" />
                    <Bar dataKey="engagement" fill="#82ca9d" name="Engagement %" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="platforms" className="space-y-6">
          <div className="grid gap-6">
            {platformData.map((platform) => {
              const Icon = platformIcons[platform.platform as keyof typeof platformIcons]
              return (
                <Card key={platform.platform}>
                  <CardHeader>
                    <div className="flex items-center space-x-3">
                      <div
                        className="p-2 rounded-lg text-white"
                        style={{ backgroundColor: platform.color }}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle>{platform.platform}</CardTitle>
                        <CardDescription>
                          {formatNumber(platform.followers)} followers
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold">{platform.posts}</div>
                        <p className="text-sm text-muted-foreground">Posts</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">{platform.engagement}%</div>
                        <p className="text-sm text-muted-foreground">Engagement</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold">{formatNumber(platform.followers)}</div>
                        <p className="text-sm text-muted-foreground">Followers</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="content" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Posts</CardTitle>
              <CardDescription>
                Your best content from the selected time period
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topPostsData.map((post, index) => {
                  const Icon = platformIcons[post.platform as keyof typeof platformIcons]
                  return (
                    <div key={post.id} className="flex items-center space-x-4 p-4 border rounded-lg">
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="text-lg font-semibold text-muted-foreground">
                          #{index + 1}
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold">{post.title}</h3>
                          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                            <Icon className="h-4 w-4" />
                            <span>{post.platform}</span>
                            <span>•</span>
                            <span>{new Date(post.date).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-6 text-sm">
                        <div className="text-center">
                          <div className="font-semibold">{formatNumber(post.views)}</div>
                          <div className="text-muted-foreground">Views</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold">{post.likes}</div>
                          <div className="text-muted-foreground">Likes</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold">{post.comments}</div>
                          <div className="text-muted-foreground">Comments</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold">{post.engagement}%</div>
                          <div className="text-muted-foreground">Engagement</div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audience" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Audience Demographics</CardTitle>
                <CardDescription>
                  Age distribution of your audience
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={audienceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="percentage" fill="#8884d8" name="Percentage" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Audience Growth</CardTitle>
                <CardDescription>
                  Follower growth over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={engagementData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="views"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Audience Insights</CardTitle>
              <CardDescription>
                Key insights about your audience
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold">25-34</div>
                  <p className="text-sm text-muted-foreground">Most active age group</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold">2:00 PM</div>
                  <p className="text-sm text-muted-foreground">Peak engagement time</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold">Tuesday</div>
                  <p className="text-sm text-muted-foreground">Best posting day</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
