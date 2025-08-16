'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle, XCircle, Mail, Loader2 } from 'lucide-react'
import Link from 'next/link'

function VerifyEmailContent() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'pending'>('loading')
  const [message, setMessage] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const supabase = createClient()

  useEffect(() => {
    const handleEmailVerification = async () => {
      const token_hash = searchParams.get('token_hash')
      const type = searchParams.get('type')
      
      if (token_hash && type) {
        try {
          const { error } = await supabase.auth.verifyOtp({
            token_hash,
            type: type as 'signup' | 'email_change',
          })

          if (error) {
            setStatus('error')
            setMessage(error.message)
          } else {
            setStatus('success')
            setMessage('Email verified successfully! Redirecting to dashboard...')
            setTimeout(() => {
              router.push('/dashboard')
            }, 2000)
          }
        } catch (error) {
          setStatus('error')
          setMessage('An unexpected error occurred')
        }
      } else {
        // No verification token, show pending verification state
        setStatus('pending')
        setMessage('Please check your email and click the verification link')
      }
    }

    handleEmailVerification()
  }, [searchParams, router, supabase.auth])

  const resendVerification = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (user?.email) {
        const { error } = await supabase.auth.resend({
          type: 'signup',
          email: user.email,
        })
        
        if (error) {
          setMessage('Failed to resend verification email')
        } else {
          setMessage('Verification email sent! Please check your inbox.')
        }
      }
    } catch (error) {
      setMessage('Failed to resend verification email')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4">
            {status === 'loading' && <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />}
            {status === 'success' && <CheckCircle className="h-12 w-12 text-green-600" />}
            {status === 'error' && <XCircle className="h-12 w-12 text-red-600" />}
            {status === 'pending' && <Mail className="h-12 w-12 text-blue-600" />}
          </div>
          <CardTitle className="text-2xl">
            {status === 'loading' && 'Verifying Email...'}
            {status === 'success' && 'Email Verified!'}
            {status === 'error' && 'Verification Failed'}
            {status === 'pending' && 'Check Your Email'}
          </CardTitle>
          <CardDescription>
            {message}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {status === 'pending' && (
            <>
              <p className="text-sm text-gray-600 text-center">
                We&apos;ve sent a verification link to your email address. Please click the link to verify your account.
              </p>
              <Button onClick={resendVerification} variant="outline" className="w-full">
                Resend Verification Email
              </Button>
            </>
          )}
          
          {status === 'error' && (
            <div className="space-y-2">
              <Button onClick={resendVerification} variant="outline" className="w-full">
                Resend Verification Email
              </Button>
              <Link href="/auth/login">
                <Button variant="ghost" className="w-full">
                  Back to Login
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

          {status === 'loading' && (
            <div className="text-center">
              <p className="text-sm text-gray-500">Please wait while we verify your email...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardContent className="p-6 text-center">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600 mb-4" />
            <p>Loading...</p>
          </CardContent>
        </Card>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  )
}
