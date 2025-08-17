import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Performance optimizations
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },

  // Turbopack configuration (stable)
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },

  // Bundle optimization
  serverExternalPackages: ['@supabase/supabase-js'],

  // Image optimization
  images: {
    domains: ['localhost', 'supabase.co'],
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 60,
  },

  // Build optimization
  compress: true,

  // ESLint configuration
  eslint: {
    dirs: ['src'],
    ignoreDuringBuilds: true, // Allow warnings during builds
  },

  // TypeScript configuration
  typescript: {
    ignoreBuildErrors: false, // Enable type checking during builds
  },

  // Headers for performance
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
}

export default nextConfig;
