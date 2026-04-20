import type { NextConfig } from "next";
import createMDX from "@next/mdx";

const nextConfig: NextConfig = {
  pageExtensions: ["ts", "tsx", "md", "mdx"],
  transpilePackages: ["@initia/interwovenkit-react"],
};

const withMDX = createMDX({});

export default withMDX(nextConfig);
