import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Bot, Calendar, BarChart3, Users, Zap, Sparkles } from "lucide-react";
import Link from "next/link";
import { env } from "@/lib/env";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <h1 className="text-xl font-bold">{env.NEXT_PUBLIC_APP_NAME}</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="ghost" asChild>
              <Link href="/auth/login">Sign In</Link>
            </Button>
            <Button asChild>
              <Link href="/auth/register">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <Badge variant="secondary" className="mb-4">
          <Bot className="w-4 h-4 mr-2" />
          AI-Powered Social Media Management
        </Badge>
        <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
          Create, Schedule & Analyze
          <br />
          Social Media Content
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          {env.NEXT_PUBLIC_APP_DESCRIPTION}. Generate engaging posts with AI, schedule across platforms, and track performance.
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
          <h2 className="text-3xl font-bold mb-4">Everything you need to succeed</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Powerful features designed to streamline your social media workflow and maximize engagement.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <Bot className="w-12 h-12 text-primary mb-4" />
              <CardTitle>AI Content Generation</CardTitle>
              <CardDescription>
                Generate engaging posts with advanced AI models. Create variations, optimize for platforms, and maintain your brand voice.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <Calendar className="w-12 h-12 text-primary mb-4" />
              <CardTitle>Smart Scheduling</CardTitle>
              <CardDescription>
                Schedule posts across multiple platforms with optimal timing suggestions and drag-and-drop calendar interface.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <BarChart3 className="w-12 h-12 text-primary mb-4" />
              <CardTitle>Advanced Analytics</CardTitle>
              <CardDescription>
                Track performance, engagement metrics, and ROI across all platforms with beautiful, actionable insights.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <Users className="w-12 h-12 text-primary mb-4" />
              <CardTitle>Team Collaboration</CardTitle>
              <CardDescription>
                Work together with your team, assign roles, review content, and maintain consistent brand messaging.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <Zap className="w-12 h-12 text-primary mb-4" />
              <CardTitle>Multi-Platform Support</CardTitle>
              <CardDescription>
                Connect and post to Twitter/X, LinkedIn, Facebook, Instagram, and more from a single dashboard.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <Sparkles className="w-12 h-12 text-primary mb-4" />
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
        <Card className="border-0 shadow-xl bg-primary text-primary-foreground">
          <CardContent className="p-12 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to transform your social media?</h2>
            <p className="text-primary-foreground/80 mb-8 max-w-2xl mx-auto">
              Join thousands of creators and businesses who are already using AI to create better content faster.
            </p>
            <Button size="lg" variant="secondary">
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
          <p>&copy; 2024 {env.NEXT_PUBLIC_APP_NAME}. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}