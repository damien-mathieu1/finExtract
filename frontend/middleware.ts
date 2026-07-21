import { NextRequest, NextResponse } from "next/server"

export const config = {
  matcher: "/api/:path*",
}

export function middleware(request: NextRequest) {
  const target = process.env.API_PROXY_TARGET || "http://localhost:8000"
  const url = new URL(request.nextUrl.pathname.replace(/^\/api/, ""), target)
  url.search = request.nextUrl.search
  return NextResponse.rewrite(url)
}
