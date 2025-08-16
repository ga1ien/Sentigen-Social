import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  serverExternalPackages: ['@supabase/supabase-js'],
  images: {
    domains: ['localhost', 'supabase.co'],
  },
}

export default nextConfig;
