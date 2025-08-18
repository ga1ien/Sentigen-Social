import { DashboardNav } from "@/components/dashboard/nav"
import { DashboardSidebar } from "@/components/dashboard/sidebar"
import { ThemeBackgrounds } from "@/components/zyyn/theme-backgrounds"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen relative overflow-hidden">
      <ThemeBackgrounds />
      <DashboardNav />
      <div className="flex">
        <div className="border-r border-white/10 bg-white/5 backdrop-blur-sm"><DashboardSidebar /></div>
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
