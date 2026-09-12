import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output: `.next/standalone` bundles only the files actually
  // needed at runtime (server.js + a pruned node_modules), so the Docker
  // image doesn't need the full devDependencies tree or source checkout.
  output: "standalone",
};

export default nextConfig;
