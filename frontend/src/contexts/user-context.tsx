"use client"

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { createClient } from '@/lib/supabase/client'
import { User, AuthChangeEvent, Session } from '@supabase/supabase-js'

interface UserContextType {
  user: User | null
  loading: boolean
  signOut: () => Promise<void>
  refreshUser: () => Promise<void>
}

const UserContext = createContext<UserContextType | undefined>(undefined)

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  const refreshUser = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
    } catch (error) {
      console.error('Error refreshing user:', error)
      setUser(null)
    }
  }

  const signOut = async () => {
    try {
      await supabase.auth.signOut()
      setUser(null)
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  useEffect(() => {
    let mounted = true

    // Get initial session
    const initializeAuth = async () => {
      try {
        // First try to get the session from storage
        const { data: { session }, error } = await supabase.auth.getSession()

        if (mounted) {
          if (error) {
            console.error('Error getting session:', error)
            setUser(null)
          } else if (session?.user) {
            setUser(session.user)
          } else {
            // If no session, try to get user
            const { data: { user } } = await supabase.auth.getUser()
            if (user && mounted) {
              setUser(user)
            }
          }
          setLoading(false)
        }
      } catch (error) {
        console.error('Error initializing auth:', error)
        if (mounted) {
          setUser(null)
          setLoading(false)
        }
      }
    }

    initializeAuth()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event: AuthChangeEvent, session: Session | null) => {
        if (!mounted) return

        // Only update if there's an actual change
        if (event === 'SIGNED_OUT') {
          setUser(null)
        } else if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
          if (session?.user) {
            setUser(session.user)
          }
        } else if (event === 'USER_UPDATED' && session?.user) {
          setUser(session.user)
        }

        // Don't set loading to false here as it can cause flicker
      }
    )

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, []) // Remove supabase.auth dependency to prevent re-initialization

  return (
    <UserContext.Provider value={{ user, loading, signOut, refreshUser }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  const context = useContext(UserContext)
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider')
  }
  return context
}
