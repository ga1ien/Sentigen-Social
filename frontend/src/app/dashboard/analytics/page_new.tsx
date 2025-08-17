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
  Youtube,
  BarChart3,
  Settings
} from 'lucide-react'

const platformIcons = {
  LinkedIn: Linkedin,
  Twitter: Twitter,
  Instagram: Instagram,
  Facebook: Facebook,
  YouTube: Youtube,
}

export default function AnalyticsPage() {
  const { user, loading } = useUser()
  const [timeRange, setTimeRange] = useState('7d')
  const [selectedPlatform, setSelectedPlatform] = useState('all')
  const [loadingData, setLoadingData] = useState(true)

  useEffect(() => {
    if (user && !loading) {
      loadAnalyticsData()
    }
  }, [user, loading, timeRange, selectedPlatform])

  const loadAnalyticsData = async () => {
    try {
      setLoadingData(true)
      // TODO: Load real analytics data from backend
      // For now, show empty state
    } catch (error) {
      console.error('Error loading analytics:', error)
    } finally {
      setLoadingData(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Analytics</h1>
            <p className="text-muted-foreground">Loading your analytics data...</p>
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
            <h1 className="text-3xl font-bold">Analytics</h1>
            <p className="text-muted-foreground">Please log in to view your analytics.</p>
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
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Track your social media performance and engagement
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select time range" />
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

      {/* Empty State */}
      <div className="flex flex-col items-center justify-center py-16">
        <BarChart3 className="h-24 w-24 text-muted-foreground mb-6" />
        <h3 className="text-2xl font-semibold mb-2">No Analytics Data Yet</h3>
        <p className="text-muted-foreground text-center max-w-md mb-6">
          Connect your social media accounts and start posting to see detailed analytics and insights about your content performance.
        </p>
        <div className="flex space-x-4">
          <Button>
            <Settings className="mr-2 h-4 w-4" />
            Connect Social Accounts
          </Button>
          <Button variant="outline">
            Create Your First Post
          </Button>
        </div>
      </div>

      {/* Platform Connection Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[
          { name: 'LinkedIn', icon: Linkedin, color: '#0077B5', connected: false },
          { name: 'Twitter', icon: Twitter, color: '#1DA1F2', connected: false },
          { name: 'Instagram', icon: Instagram, color: '#E4405F', connected: false },
          { name: 'Facebook', icon: Facebook, color: '#1877F2', connected: false },
          { name: 'YouTube', icon: Youtube, color: '#FF0000', connected: false },
        ].map((platform) => {
          const Icon = platform.icon
          return (
            <Card key={platform.name} className="relative">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <Icon className="mr-2 h-4 w-4" style={{ color: platform.color }} />
                  {platform.name}
                </CardTitle>
                <Badge variant={platform.connected ? "default" : "secondary"}>
                  {platform.connected ? "Connected" : "Not Connected"}
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-muted-foreground">--</div>
                <p className="text-xs text-muted-foreground">
                  {platform.connected ? "No data available" : "Connect to view analytics"}
                </p>
                {!platform.connected && (
                  <Button variant="outline" size="sm" className="mt-2">
                    Connect {platform.name}
                  </Button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Getting Started Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started with Analytics</CardTitle>
          <CardDescription>
            Follow these steps to start tracking your social media performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-semibold">
                1
              </div>
              <div>
                <h4 className="font-semibold">Connect Your Accounts</h4>
                <p className="text-sm text-muted-foreground">
                  Link your social media accounts to start collecting data
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-semibold">
                2
              </div>
              <div>
                <h4 className="font-semibold">Create Content</h4>
                <p className="text-sm text-muted-foreground">
                  Start posting content to generate engagement data
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-semibold">
                3
              </div>
              <div>
                <h4 className="font-semibold">Track Performance</h4>
                <p className="text-sm text-muted-foreground">
                  Monitor your analytics and optimize your strategy
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
