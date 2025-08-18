"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  Home,
  BarChart3,
  Brain,
  Image,
  Calendar,
  Users,
  Settings,
  Bell,
  Search,
  Plus
} from "lucide-react"

const navItems = [
  { icon: Home, label: "home", href: "/dashboard" },
  { icon: BarChart3, label: "analytics", href: "/dashboard/analytics" },
  { icon: Brain, label: "intelligence", href: "/dashboard/intelligence" },
  { icon: Image, label: "media", href: "/dashboard/media" },
  { icon: Calendar, label: "calendar", href: "/dashboard/calendar" },
  { icon: Users, label: "team", href: "/dashboard/team" },
]

export function SpatialNav() {
  const pathname = usePathname()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <>
      {/* Top Bar */}
      <div className={cn(
        "fixed top-0 left-0 right-0 z-40 transition-all duration-300",
        scrolled ? "bg-black/20 backdrop-blur-xl border-b border-white/10" : "bg-transparent"
      )}>
        <div className="flex items-center justify-between px-6 h-14">
          {/* Logo */}
          <Link href="/dashboard" className="text-white/90 text-sm font-light tracking-wide">
            zyyn
          </Link>

          {/* Center Actions */}
          <div className="flex items-center gap-2">
            <button className="p-2 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all">
              <Search className="w-4 h-4 text-white/60" />
            </button>
            <button className="px-3 py-1.5 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/15 transition-all flex items-center gap-2">
              <Plus className="w-4 h-4 text-white/80" />
              <span className="text-sm text-white/80">create</span>
            </button>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            <button className="relative p-2 rounded-xl hover:bg-white/10 transition-all">
              <Bell className="w-4 h-4 text-white/60" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-500 rounded-full" />
            </button>
            <button className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600" />
          </div>
        </div>
      </div>

      {/* Bottom Navigation - Mobile/Tablet */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 lg:hidden">
        <div className="flex items-center gap-1 p-1.5 rounded-2xl bg-white/10 backdrop-blur-xl border border-white/20">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center w-14 h-14 rounded-xl transition-all",
                  isActive ? "bg-white/20" : "hover:bg-white/10"
                )}
              >
                <Icon className={cn(
                  "w-5 h-5 mb-1",
                  isActive ? "text-white" : "text-white/60"
                )} />
                <span className={cn(
                  "text-[10px]",
                  isActive ? "text-white/90" : "text-white/50"
                )}>
                  {item.label}
                </span>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Side Navigation - Desktop */}
      <div className="hidden lg:flex fixed left-6 top-1/2 -translate-y-1/2 z-40">
        <div className="flex flex-col gap-2 p-2 rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group relative flex items-center justify-center w-12 h-12 rounded-xl transition-all",
                  isActive ? "bg-white/15" : "hover:bg-white/10"
                )}
              >
                <Icon className={cn(
                  "w-5 h-5",
                  isActive ? "text-white" : "text-white/60"
                )} />

                {/* Tooltip */}
                <span className="absolute left-full ml-3 px-2 py-1 bg-black/80 backdrop-blur-sm rounded-lg text-xs text-white/90 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap">
                  {item.label}
                </span>
              </Link>
            )
          })}

          <div className="h-px bg-white/10 my-2" />

          <Link
            href="/dashboard/settings"
            className={cn(
              "group relative flex items-center justify-center w-12 h-12 rounded-xl transition-all",
              pathname === "/dashboard/settings" ? "bg-white/15" : "hover:bg-white/10"
            )}
          >
            <Settings className={cn(
              "w-5 h-5",
              pathname === "/dashboard/settings" ? "text-white" : "text-white/60"
            )} />
            <span className="absolute left-full ml-3 px-2 py-1 bg-black/80 backdrop-blur-sm rounded-lg text-xs text-white/90 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
              settings
            </span>
          </Link>
        </div>
      </div>
    </>
  )
}
