"use client"

import { useState } from "react";
import { GlassCard, GlassCardContent, GlassCardDescription, GlassCardHeader, GlassCardTitle } from "@/components/zyyn/glass-card";
import { AuthModal } from "@/components/zyyn/auth-modal";
import { ArrowRight, Bot, Calendar, BarChart3, Users, Zap, Sparkles } from "lucide-react";
import Link from "next/link";

export default function HomePage() {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="text-white text-lg font-light tracking-wide">
              zyyn
            </Link>
            <div className="flex items-center gap-4">
              <button
                onClick={() => {
                  setAuthMode("signin");
                  setAuthModalOpen(true);
                }}
                className="px-4 py-2 text-sm text-white/85 hover:text-white transition-colors"
              >
                sign in
              </button>
              <button
                onClick={() => {
                  setAuthMode("signup");
                  setAuthModalOpen(true);
                }}
                className="px-4 py-2 text-sm bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl hover:bg-white/15 transition-all text-white"
              >
                get started
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="flex-1 flex items-center justify-center px-4 pt-24 pb-16">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/20">
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-white/80">ai-native</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extralight text-white tracking-tight">
            zyyn
          </h1>

          <p className="text-xl md:text-2xl text-white/80 font-light max-w-2xl mx-auto">
            create at the speed of thought
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8">
            <button
              onClick={() => {
                setAuthMode("signup");
                setAuthModalOpen(true);
              }}
              className="group px-8 py-3 bg-white/15 backdrop-blur-sm border border-white/30 rounded-2xl hover:bg-white/20 transition-all flex items-center gap-2 text-white"
            >
              start creating
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <Link
              href="#features"
              className="px-8 py-3 text-white/85 hover:text-white transition-colors"
            >
              view demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-6xl mx-auto space-y-16">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-light text-white">
              less, but better
            </h2>
            <p className="text-lg text-white/80 max-w-2xl mx-auto">
              clean, spatial interfaces for content creation, scheduling, and insights
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <GlassCard variant="elevated" blur="lg" glow className="group hover:scale-[1.02] transition-transform">
              <GlassCardHeader>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-4">
                  <Bot className="w-6 h-6 text-white/80" />
                </div>
                <GlassCardTitle>ai content generation</GlassCardTitle>
                <GlassCardDescription>
                  generate engaging posts with advanced ai models. create variations, optimize for platforms, and maintain your brand voice.
                </GlassCardDescription>
              </GlassCardHeader>
            </GlassCard>

            <GlassCard variant="elevated" blur="lg" glow className="group hover:scale-[1.02] transition-transform">
              <GlassCardHeader>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500/20 to-blue-500/20 flex items-center justify-center mb-4">
                  <Calendar className="w-6 h-6 text-white/80" />
                </div>
                <GlassCardTitle>smart scheduling</GlassCardTitle>
                <GlassCardDescription>
                  schedule posts across multiple platforms with optimal timing suggestions and drag-and-drop calendar interface.
                </GlassCardDescription>
              </GlassCardHeader>
            </GlassCard>

            <GlassCard variant="elevated" blur="lg" glow className="group hover:scale-[1.02] transition-transform">
              <GlassCardHeader>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center mb-4">
                  <BarChart3 className="w-6 h-6 text-white/80" />
                </div>
                <GlassCardTitle>advanced analytics</GlassCardTitle>
                <GlassCardDescription>
                  track performance, engagement metrics, and roi across all platforms with beautiful, actionable insights.
                </GlassCardDescription>
              </GlassCardHeader>
            </GlassCard>

            <GlassCard variant="elevated" blur="lg" glow className="group hover:scale-[1.02] transition-transform">
              <GlassCardHeader>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 flex items-center justify-center mb-4">
                  <Users className="w-6 h-6 text-white/80" />
                </div>
                <GlassCardTitle>team collaboration</GlassCardTitle>
                <GlassCardDescription>
                  work together with your team, assign roles, review content, and maintain consistent brand messaging.
                </GlassCardDescription>
              </GlassCardHeader>
            </GlassCard>

            <GlassCard variant="elevated" blur="lg" glow className="group hover:scale-[1.02] transition-transform">
              <GlassCardHeader>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-yellow-500/20 to-orange-500/20 flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-white/80" />
                </div>
                <GlassCardTitle>multi-platform support</GlassCardTitle>
                <GlassCardDescription>
                  connect and post to twitter/x, linkedin, facebook, instagram, and more from a single dashboard.
                </GlassCardDescription>
              </GlassCardHeader>
            </GlassCard>

            <GlassCard variant="elevated" blur="lg" glow className="group hover:scale-[1.02] transition-transform">
              <GlassCardHeader>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-white/80" />
                </div>
                <GlassCardTitle>rich media editor</GlassCardTitle>
                <GlassCardDescription>
                  create stunning posts with our rich text editor, image uploads, emoji picker, and media management.
                </GlassCardDescription>
              </GlassCardHeader>
            </GlassCard>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <GlassCard variant="elevated" blur="xl" glow className="p-12">
            <h2 className="text-3xl md:text-4xl font-light text-white mb-4">
              ready to be seen?
            </h2>
            <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto">
              join thousands of creators using zyyn to amplify their voice and grow their audience
            </p>
            <button
              onClick={() => {
                setAuthMode("signup");
                setAuthModalOpen(true);
              }}
              className="inline-flex items-center gap-2 px-8 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-2xl hover:bg-white/25 transition-all text-white"
            >
              get started free
              <ArrowRight className="w-4 h-4" />
            </button>
          </GlassCard>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-white/10">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-white/70">© 2025 zyyn. all rights reserved.</p>
          <div className="flex items-center gap-6">
            <Link href="#" className="text-sm text-white/70 hover:text-white/85 transition-colors">
              privacy
            </Link>
            <Link href="#" className="text-sm text-white/70 hover:text-white/85 transition-colors">
              terms
            </Link>
            <Link href="#" className="text-sm text-white/70 hover:text-white/85 transition-colors">
              contact
            </Link>
          </div>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        defaultMode={authMode}
      />
    </div>
  );
}
