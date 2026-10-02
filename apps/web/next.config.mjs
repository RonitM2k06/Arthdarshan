/** @type {import('next').NextConfig} */
const API = process.env.ARTH_API_URL || "http://127.0.0.1:8000";
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    // The browser only ever talks to this origin; Next proxies /api to the local FastAPI server (no CORS, works offline).
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};
export default nextConfig;
