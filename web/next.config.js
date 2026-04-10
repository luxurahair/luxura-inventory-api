/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['static.wixstatic.com', 'customer-assets.emergentagent.com', 'localhost'],
  },
}

module.exports = nextConfig
