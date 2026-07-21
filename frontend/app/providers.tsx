'use client'

import { useAuth } from '@clerk/nextjs'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { setAuthTokenGetter } from '@/lib/api/auth-token'
import { LocaleProvider } from '@/lib/i18n'

function AuthTokenBridge() {
  const { getToken } = useAuth()
  useEffect(() => {
    setAuthTokenGetter(getToken)
  }, [getToken])
  return null
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())
  return (
    <QueryClientProvider client={queryClient}>
      <AuthTokenBridge />
      <LocaleProvider>{children}</LocaleProvider>
    </QueryClientProvider>
  )
}
