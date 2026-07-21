// Bridges Clerk's hook-based getToken to the plain-function API client:
// client.ts is called outside React, so a component (AuthTokenBridge in
// providers.tsx) registers the getter at mount.
type TokenGetter = () => Promise<string | null>

let getter: TokenGetter | null = null

export function setAuthTokenGetter(fn: TokenGetter) {
  getter = fn
}

export async function getAuthToken(): Promise<string | null> {
  if (getter) return getter()
  // The ClerkLoaded gate in layout.tsx guarantees window.Clerk exists
  // before the app renders, so this fallback covers the pre-bridge window.
  if (typeof window !== 'undefined') {
    const clerk = (window as { Clerk?: { session?: { getToken(): Promise<string | null> } } })
      .Clerk
    return (await clerk?.session?.getToken()) ?? null
  }
  return null
}
