"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Home,
  PenTool,
  Calendar,
  BarChart3,
  Settings,
  Users,
  Image,
  Video,
  Bot,
  Zap,
  Brain,
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

const sidebarItems = [
  {
    title: "Overview",
    href: "/dashboard",
    icon: Home,
  },
  {
    title: "Content Creator",
    href: "/dashboard/create",
    icon: PenTool,
    badge: "AI",
  },
  {
    title: "Pipeline (new)",
    href: "/dashboard/create/pipeline",
    icon: Zap,
    badge: "v1",
  },
  {
    title: "Calendar",
    href: "/dashboard/calendar",
    icon: Calendar,
  },
  {
    title: "Analytics",
    href: "/dashboard/analytics",
    icon: BarChart3,
  },
  {
    title: "Intelligence",
    href: "/dashboard/intelligence",
    icon: Brain,
    badge: "AI",
  },
  {
    title: "Media Library",
    href: "/dashboard/media",
    icon: Image,
  },
  {
    title: "AI Tools",
    href: "/dashboard/ai-tools",
    icon: Bot,
    badge: "New",
  },
  {
    title: "AI Avatars",
    href: "/dashboard/avatars",
    icon: Video,
    badge: "AI",
  },
  {
    title: "Research-to-Video",
    href: "/dashboard/research-video",
    icon: Zap,
    badge: "New",
  },
  {
    title: "Team",
    href: "/dashboard/team",
    icon: Users,
  },
  {
    title: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
  },
]

export function DashboardSidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 p-4">
      <nav className="space-y-2">
        {sidebarItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Button
              key={item.href}
              variant={isActive ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start border border-white/10 bg-white/5 backdrop-blur-sm",
                isActive && "bg-white/10"
              )}
              asChild
            >
              <Link href={item.href}>
                <item.icon className="mr-2 h-4 w-4" />
                {item.title}
                {item.badge && (
                  <Badge variant="secondary" className="ml-auto">
                    {item.badge}
                  </Badge>
                )}
              </Link>
            </Button>
          )
        })}
      </nav>

      {/* Quick Actions */}
      <div className="mt-8 space-y-4">
        <h3 className="text-sm font-medium text-muted-foreground">Quick Actions</h3>
        <div className="space-y-2">
          <Button variant="outline" size="sm" className="w-full justify-start border-white/10 bg-white/5 backdrop-blur-sm">
            <Zap className="mr-2 h-4 w-4" />
            Generate Post
          </Button>
          <Button variant="outline" size="sm" className="w-full justify-start border-white/10 bg-white/5 backdrop-blur-sm">
            <Video className="mr-2 h-4 w-4" />
            Create Video
          </Button>
        </div>
      </div>
    </div>
  )
}
