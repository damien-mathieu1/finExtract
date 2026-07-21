import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server"
import { NextResponse } from "next/server"

// "/" is public: it renders the landing page for signed-out visitors and
// the app for signed-in users (SignedIn/SignedOut split in app/page.tsx).
// The API stays fully protected — the backend verifies the JWT itself.
const isPublicRoute = createRouteMatcher(["/", "/sign-in(.*)"])

// Auth gate + API proxy in one middleware: everything except /sign-in
// requires a Clerk session, and /api/* is rewritten to the FastAPI backend
// (which re-verifies the JWT itself — its URL is public).
export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) await auth.protect()
  if (request.nextUrl.pathname.startsWith("/api/")) {
    const target = process.env.API_PROXY_TARGET || "http://localhost:8000"
    const url = new URL(request.nextUrl.pathname.replace(/^\/api/, ""), target)
    url.search = request.nextUrl.search
    return NextResponse.rewrite(url)
  }
})

export const config = {
  matcher: [
    // All routes except Next internals and static assets
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/api/:path*",
  ],
}
