'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Loader2 } from 'lucide-react'

function AuthCallbackContent() {
  const [message, setMessage] = useState('authenticating...')
  const router = useRouter()
  const searchParams = useSearchParams()
  const supabase = createClient()

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        const code = searchParams.get('code')
        const error = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')

        if (error) {
          setMessage(errorDescription || error)
          // Redirect to home with error message after a brief delay
          setTimeout(() => {
            router.push('/?error=' + encodeURIComponent(errorDescription || error))
          }, 2000)
          return
        }

        if (code) {
          const { data, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)

          if (exchangeError) {
            setMessage(exchangeError.message)
            setTimeout(() => {
              router.push('/?error=' + encodeURIComponent(exchangeError.message))
            }, 2000)
            return
          }

          if (data.session) {
            setMessage('welcome back! redirecting...')
            // Immediate redirect to dashboard
            router.push('/dashboard')
          }
        } else {
          // Handle other auth flows (like email confirmation)
          const { data: { session }, error: sessionError } = await supabase.auth.getSession()

          if (sessionError) {
            setMessage(sessionError.message)
            setTimeout(() => {
              router.push('/?error=' + encodeURIComponent(sessionError.message))
            }, 2000)
          } else if (session) {
            setMessage('welcome back! redirecting...')
            router.push('/dashboard')
          } else {
            setMessage('no active session')
            setTimeout(() => {
              router.push('/')
            }, 2000)
          }
        }
      } catch (error) {
        setMessage('something went wrong')
        setTimeout(() => {
          router.push('/?error=authentication_failed')
        }, 2000)
      }
    }

    handleAuthCallback()
  }, [searchParams, router, supabase.auth])

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="text-center space-y-4">
        <Loader2 className="h-8 w-8 text-gray-700 animate-spin mx-auto" />
        <p className="text-gray-700 font-light">{message}</p>
      </div>
    </div>
  )
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 text-gray-700 animate-spin mx-auto" />
          <p className="text-gray-700 font-light">loading...</p>
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  )
}
