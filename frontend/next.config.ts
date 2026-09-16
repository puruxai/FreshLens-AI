import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // 1. If explicit NEXT_PUBLIC_API_URL is set, use it for cross-origin API routing
    if (process.env.NEXT_PUBLIC_API_URL) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
      return [
        {
          source: "/api/v1/:path*",
          destination: `${apiUrl}/api/v1/:path*`,
        },
        {
          source: "/static/uploads/:path*",
          destination: `${apiUrl}/static/uploads/:path*`,
        },
        {
          source: "/docs",
          destination: `${apiUrl}/docs`,
        },
        {
          source: "/openapi.json",
          destination: `${apiUrl}/openapi.json`,
        },
        {
          source: "/health",
          destination: `${apiUrl}/health`,
        },
      ];
    }

    // 2. If running on Vercel (same-origin API serverless functions via vercel.json),
    // skip rewrites so Vercel handles /api/v1 and API routes natively.
    if (process.env.VERCEL || process.env.VERCEL_ENV) {
      return [];
    }

    // 3. Fallback for local development or Docker container environment
    const targetBackend = process.env.DOCKER_ENV === "true"
      ? "http://backend:8000"
      : "http://localhost:8000";

    return [
      {
        source: "/api/v1/:path*",
        destination: `${targetBackend}/api/v1/:path*`,
      },
      {
        source: "/static/uploads/:path*",
        destination: `${targetBackend}/static/uploads/:path*`,
      },
      {
        source: "/docs",
        destination: `${targetBackend}/docs`,
      },
      {
        source: "/openapi.json",
        destination: `${targetBackend}/openapi.json`,
      },
      {
        source: "/health",
        destination: `${targetBackend}/health`,
      },
    ];
  },
};

export default nextConfig;
