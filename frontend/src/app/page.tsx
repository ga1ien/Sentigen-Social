import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Bot, Calendar, BarChart3, Users, Zap } from "lucide-react";
import Link from "next/link";
import { env } from "@/lib/env";

export default function HomePage() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Moving background */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(1000px_600px_at_0%_-10%,hsl(var(--primary)/0.15),transparent),radial-gradient(800px_500px_at_100%_0%,hsl(var(--secondary)/0.15),transparent)] animate-[pulse_10s_ease-in-out_infinite]" />
        <div className="absolute inset-0 bg-gradient-to-b from-background/60 to-background" />
      </div>

      {/* Minimal header */}
      <header className="border-b bg-background/70 backdrop-blur supports-[backdrop-filter]:bg-background/40">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold tracking-wide lowercase">{env.NEXT_PUBLIC_APP_NAME}</h1>
          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild>
              <Link href="/auth/login">Sign in</Link>
            </Button>
            <Button asChild>
              <Link href="/auth/register">Get started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <Badge variant="secondary" className="mb-4">AI-native</Badge>
        <h1 className="text-4xl md:text-6xl font-semibold mb-6 tracking-tight">zyyn</h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto lowercase">
          {env.NEXT_PUBLIC_APP_DESCRIPTION}
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" asChild>
            <Link href="/auth/register">
              Start Creating <ArrowRight className="ml-2 w-4 h-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/demo">View Demo</Link>
          </Button>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-semibold mb-4">Less, but better</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Clean, spatial interfaces for content creation, scheduling, and insights.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <Card className="border border-white/10 bg-white/5 backdrop-blur-sm shadow-[0_0_1px_rgba(255,255,255,0.2)]">
            <CardHeader>
              <Bot className="w-12 h-12 text-primary mb-4" />
              <CardTitle>AI Content Generation</CardTitle>
              <CardDescription>
                Generate engaging posts with advanced AI models. Create variations, optimize for platforms, and maintain your brand voice.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border border-white/10 bg-white/5 backdrop-blur-sm shadow-[0_0_1px_rgba(255,255,255,0.2)]">
            <CardHeader>
              <Calendar className="w-12 h-12 text-primary mb-4" />
              <CardTitle>Smart Scheduling</CardTitle>
              <CardDescription>
                Schedule posts across multiple platforms with optimal timing suggestions and drag-and-drop calendar interface.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border border-white/10 bg-white/5 backdrop-blur-sm shadow-[0_0_1px_rgba(255,255,255,0.2)]">
            <CardHeader>
              <BarChart3 className="w-12 h-12 text-primary mb-4" />
              <CardTitle>Advanced Analytics</CardTitle>
              <CardDescription>
                Track performance, engagement metrics, and ROI across all platforms with beautiful, actionable insights.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border border-white/10 bg-white/5 backdrop-blur-sm shadow-[0_0_1px_rgba(255,255,255,0.2)]">
            <CardHeader>
              <Users className="w-12 h-12 text-primary mb-4" />
              <CardTitle>Team Collaboration</CardTitle>
              <CardDescription>
                Work together with your team, assign roles, review content, and maintain consistent brand messaging.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border border-white/10 bg-white/5 backdrop-blur-sm shadow-[0_0_1px_rgba(255,255,255,0.2)]">
            <CardHeader>
              <CardTitle>Rich Media Editor</CardTitle>
              <CardDescription>
                Create stunning posts with our rich text editor, image uploads, emoji picker, and media management.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <Card className="border border-white/10 bg-white/10 backdrop-blur text-foreground">
          <CardContent className="p-12 text-center">
            <h2 className="text-3xl font-semibold mb-4">Create at the speed of thought</h2>
            <p className="text-muted-foreground mb-8 max-w-2xl mx-auto lowercase">{env.NEXT_PUBLIC_APP_DESCRIPTION}</p>
            <Button size="lg">
              <Link href="/auth/register">
                Get Started Free <ArrowRight className="ml-2 w-4 h-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="container mx-auto px-4 py-8 text-center text-muted-foreground">
          <p className="lowercase">&copy; 2024 {env.NEXT_PUBLIC_APP_NAME}. all rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
