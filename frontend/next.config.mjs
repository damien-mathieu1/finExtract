/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    const target = process.env.API_PROXY_TARGET || 'http://localhost:8000'
    return [{ source: '/api/:path*', destination: `${target}/:path*` }]
  },
}

export default nextConfig
