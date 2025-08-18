import { DashboardNav } from "@/components/dashboard/nav"
import { DashboardSidebar } from "@/components/dashboard/sidebar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Moving background for dashboard */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(1000px_600px_at_0%_-10%,hsl(var(--primary)/0.12),transparent),radial-gradient(800px_500px_at_100%_0%,hsl(var(--secondary)/0.12),transparent)] animate-[pulse_12s_ease-in-out_infinite]" />
        <div className="absolute inset-0 bg-gradient-to-b from-background/60 to-background" />
      </div>
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
