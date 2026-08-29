/** @type {import('next').NextConfig} */
const isStaticExport = process.env.BUILD_EXPORT === '1'
const backendUrl = process.env.AKSARA_BACKEND_URL || 'http://127.0.0.1:8000'

const nextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
  // `output: export` cannot be combined with rewrites. The no-Docker launcher
  // enables it only while producing backend/app/static; dev mode keeps this
  // same-origin proxy so browser code never calls a visitor's localhost API.
  ...(isStaticExport
    ? {
        output: 'export',
        trailingSlash: true,
      }
    : {
        async rewrites() {
          return [
            {
              source: '/api/:path*',
              destination: `${backendUrl}/api/:path*`,
            },
          ]
        },
      }),
}

module.exports = nextConfig
