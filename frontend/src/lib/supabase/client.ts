import { createBrowserClient } from '@supabase/ssr'
import { env } from '@/lib/env'

export const createClient = () => {
  const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  
  if (!supabaseUrl || !supabaseAnonKey) {
    // Return a mock client for build time
    return {
      auth: {
        signInWithPassword: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
        signUp: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
        signOut: () => Promise.resolve({ error: null }),
        getSession: () => Promise.resolve({ data: { session: null }, error: null }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
        verifyOtp: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
        resetPasswordForEmail: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
        updateUser: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
        resend: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
      },
      from: () => ({
        select: () => Promise.resolve({ data: [], error: null }),
        insert: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
        update: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
        delete: () => Promise.resolve({ data: null, error: new Error('Supabase not configured') }),
      }),
    } as any
  }
  
  return createBrowserClient(supabaseUrl, supabaseAnonKey)
}
