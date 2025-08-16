'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, CheckCircle, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function AuthCallbackPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('Processing authentication...')
  const router = useRouter()
  const searchParams = useSearchParams()
  const supabase = createClient()

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        const code = searchParams.get('code')
        const error = searchParams.get('error')
        const error_description = searchParams.get('error_description')

        if (error) {
          setStatus('error')
          setMessage(error_description || error)
          return
        }

        if (code) {
          const { data, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)
          
          if (exchangeError) {
            setStatus('error')
            setMessage(exchangeError.message)
            return
          }

          if (data.session) {
            setStatus('success')
            setMessage('Authentication successful! Redirecting to dashboard...')
            
            // Small delay to show success message
            setTimeout(() => {
              router.push('/dashboard')
            }, 1500)
          }
        } else {
          // Handle other auth flows (like email confirmation)
          const { data: { session }, error: sessionError } = await supabase.auth.getSession()
          
          if (sessionError) {
            setStatus('error')
            setMessage(sessionError.message)
          } else if (session) {
            setStatus('success')
            setMessage('Authentication successful! Redirecting to dashboard...')
            setTimeout(() => {
              router.push('/dashboard')
            }, 1500)
          } else {
            setStatus('error')
            setMessage('No active session found')
          }
        }
      } catch (error) {
        setStatus('error')
        setMessage('An unexpected error occurred during authentication')
      }
    }

    handleAuthCallback()
  }, [searchParams, router, supabase.auth])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4">
            {status === 'loading' && <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />}
            {status === 'success' && <CheckCircle className="h-12 w-12 text-green-600" />}
            {status === 'error' && <XCircle className="h-12 w-12 text-red-600" />}
          </div>
          <CardTitle className="text-2xl">
            {status === 'loading' && 'Processing...'}
            {status === 'success' && 'Success!'}
            {status === 'error' && 'Authentication Failed'}
          </CardTitle>
          <CardDescription>
            {message}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {status === 'error' && (
            <div className="space-y-2">
              <Link href="/auth/login">
                <Button className="w-full">
                  Back to Login
                </Button>
              </Link>
              <Link href="/auth/register">
                <Button variant="outline" className="w-full">
                  Create Account
                </Button>
              </Link>
            </div>
          )}
          
          {status === 'success' && (
            <Link href="/dashboard">
              <Button className="w-full">
                Continue to Dashboard
              </Button>
            </Link>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
