import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  distDir: 'out',
  basePath: '/durg-compatiblity',
  assetPrefix: '/durg-compatiblity/',
  images: {
    unoptimized: true
  }
};

export default nextConfig;
