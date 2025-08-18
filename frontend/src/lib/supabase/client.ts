import { createBrowserClient } from '@supabase/ssr'
import { env } from '@/lib/env'

// Singleton instance to maintain consistent auth state
let supabaseInstance: ReturnType<typeof createBrowserClient> | null = null

export const createClient = () => {
  // Return existing instance if already created
  if (supabaseInstance) {
    return supabaseInstance
  }

  const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    // Production-ready error handling - don't return mock client
    console.error('Supabase configuration missing. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.')
    throw new Error('Supabase not configured. Please check your environment variables.')
  }

  // Create and store the singleton instance
  supabaseInstance = createBrowserClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      storageKey: 'zyyn-auth-token',
      storage: typeof window !== 'undefined' ? window.localStorage : undefined,
      autoRefreshToken: true,
      detectSessionInUrl: true
    }
  })

  return supabaseInstance
}
