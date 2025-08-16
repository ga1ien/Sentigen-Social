import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
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

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's what's happening with your social media.
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
            <div className="text-2xl font-bold">127</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+12%</span> from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">23</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-blue-600">+5</span> this week
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Engagement</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8.2%</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+2.1%</span> from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Followers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12.4K</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+573</span> this month
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Activity */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Your latest posts and their performance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              {
                title: "AI-generated post about productivity tips",
                platform: "LinkedIn",
                time: "2 hours ago",
                engagement: { views: 1234, likes: 89, comments: 12, shares: 5 },
                status: "published",
              },
              {
                title: "Behind the scenes video",
                platform: "Instagram",
                time: "5 hours ago",
                engagement: { views: 2567, likes: 156, comments: 23, shares: 12 },
                status: "published",
              },
              {
                title: "Weekly newsletter announcement",
                platform: "Twitter",
                time: "1 day ago",
                engagement: { views: 892, likes: 34, comments: 8, shares: 3 },
                status: "published",
              },
            ].map((post, index) => (
              <div key={index} className="flex items-center space-x-4 p-4 border rounded-lg">
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium leading-none">{post.title}</p>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">{post.platform}</Badge>
                    <Badge variant={post.status === "published" ? "default" : "secondary"}>
                      {post.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{post.time}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <div className="flex items-center space-x-1">
                    <Eye className="h-3 w-3" />
                    <span>{post.engagement.views}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Heart className="h-3 w-3" />
                    <span>{post.engagement.likes}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <MessageCircle className="h-3 w-3" />
                    <span>{post.engagement.comments}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Share className="h-3 w-3" />
                    <span>{post.engagement.shares}</span>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>This Week</CardTitle>
            <CardDescription>
              Your performance summary
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Posts Published</span>
                <span className="font-medium">8 / 10</span>
              </div>
              <Progress value={80} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Engagement Goal</span>
                <span className="font-medium">6.2% / 8%</span>
              </div>
              <Progress value={77.5} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Follower Growth</span>
                <span className="font-medium">143 / 200</span>
              </div>
              <Progress value={71.5} className="h-2" />
            </div>

            <div className="pt-4 space-y-2">
              <h4 className="text-sm font-medium">Top Performing Platform</h4>
              <div className="flex items-center justify-between">
                <Badge>LinkedIn</Badge>
                <span className="text-sm text-muted-foreground">12.4% engagement</span>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Best Posting Time</h4>
              <p className="text-sm text-muted-foreground">
                Tuesday, 2:00 PM - 4:00 PM
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Get started with common tasks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <PenTool className="h-6 w-6" />
              <span>Create Post</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <Calendar className="h-6 w-6" />
              <span>Schedule Content</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <BarChart3 className="h-6 w-6" />
              <span>View Analytics</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <Users className="h-6 w-6" />
              <span>Manage Team</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
