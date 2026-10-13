/** Static export: the whole app is plain files, so it runs on Vercel, GitHub Pages or a USB stick. */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
};
export default nextConfig;
