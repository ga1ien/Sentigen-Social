import { createBrowserClient } from '@supabase/ssr'
import { env } from '@/lib/env'

export const createClient = () => {
  const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    // Production-ready error handling - don't return mock client
    console.error('Supabase configuration missing. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.')
    throw new Error('Supabase not configured. Please check your environment variables.')
  }

  return createBrowserClient(supabaseUrl, supabaseAnonKey)
}
