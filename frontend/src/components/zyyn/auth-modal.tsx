"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs"
import { useToast } from "@/hooks/use-toast"

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  defaultMode?: "signin" | "signup"
}

export function AuthModal({ isOpen, onClose, defaultMode = "signin" }: AuthModalProps) {
  const [mode, setMode] = useState(defaultMode)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { toast } = useToast()
  const supabase = createClientComponentClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (mode === "signin") {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (error) throw error

        toast({
          title: "welcome back",
          description: "redirecting to dashboard...",
        })
        onClose() // Close the modal
        router.push("/dashboard")
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        })
        if (error) throw error

        toast({
          title: "check your email",
          description: "we sent you a verification link",
        })
      }
    } catch (error: any) {
      toast({
        title: "error",
        description: error.message,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-sm">
        <div className="relative rounded-3xl border border-white/20 bg-white/10 backdrop-blur-xl p-8 shadow-2xl">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute right-4 top-4 p-2 rounded-xl hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4 text-gray-700" />
          </button>

          {/* Content */}
          <div className="space-y-6">
            <div className="space-y-2 text-center">
              <h2 className="text-2xl font-light text-gray-900">
                {mode === "signin" ? "welcome back" : "get started"}
              </h2>
              <p className="text-sm text-gray-700">
                {mode === "signin"
                  ? "sign in to your account"
                  : "create your account"}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <input
                  type="email"
                  placeholder="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-white/5 backdrop-blur-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-all"
                  required
                />
              </div>

              <div>
                <input
                  type="password"
                  placeholder="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-white/5 backdrop-blur-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-all"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className={cn(
                  "w-full py-3 rounded-xl font-light transition-all",
                  "bg-white/15 backdrop-blur-sm border border-gray-300",
                  "hover:bg-white/20 text-gray-900",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                {loading ? "..." : mode === "signin" ? "sign in" : "create account"}
              </button>
            </form>

            <div className="text-center">
              <button
                onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
                className="text-sm text-gray-700 hover:text-gray-900 transition-colors"
              >
                {mode === "signin"
                  ? "need an account? sign up"
                  : "already have an account? sign in"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
