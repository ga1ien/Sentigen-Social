import { CloudBackground } from "@/components/zyyn/cloud-background"
import { SpatialNav } from "@/components/zyyn/spatial-nav"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen relative">
      <CloudBackground />
      <SpatialNav />
      <main className="pt-20 pb-24 lg:pb-8 lg:pl-24 lg:pr-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  )
}
