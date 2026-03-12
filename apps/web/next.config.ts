import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone = for Docker/Vercel; Netlify uses default output
  ...(process.env.NETLIFY ? {} : { output: "standalone" as const }),
  images: {
    remotePatterns: [{ protocol: "https", hostname: "i.postimg.cc", pathname: "/**" }],
  },
  // In dev, proxy /api/* to the local FastAPI backend so "Analyse" works without .env
  async rewrites() {
    if (process.env.NODE_ENV === "development") {
      return [{ source: "/api/:path*", destination: "http://127.0.0.1:8080/:path*" }];
    }
    return [];
  },
};

export default nextConfig;
