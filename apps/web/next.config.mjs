const apiServerUrl = process.env.API_SERVER_URL?.replace(/\/+$/, "");

const nextConfig = {
  experimental: {
    typedRoutes: true
  },
  async rewrites() {
    if (!apiServerUrl) {
      return [];
    }
    return [
      {
        source: "/api/backend/:path*",
        destination: `${apiServerUrl}/:path*`
      }
    ];
  }
};

export default nextConfig;
