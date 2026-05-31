/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || 'https://nhansinhquan.vn',
  generateRobotsTxt: false, // managed manually at public/robots.txt
  sitemapSize: 5000,
  changefreq: 'weekly',
  priority: 0.7,
  exclude: [
    '/admin',
    '/admin/*',
    '/my-account',
    '/my-account/*',
    '/check-out',
    '/check-out/*',
    '/api/*',
    '/ket-qua',
    '/404',
    '/login',
    '/register',
    '/forgot-password',
    '/reset-password',
  ],
  // Legal pages get higher priority for indexing
  additionalPaths: async (config) => [
    { loc: '/terms', changefreq: 'monthly', priority: 0.5, lastmod: '2025-05-26' },
    { loc: '/privacy', changefreq: 'monthly', priority: 0.5, lastmod: '2025-05-26' },
    { loc: '/refund-policy', changefreq: 'monthly', priority: 0.5, lastmod: '2025-05-26' },
    { loc: '/contact', changefreq: 'monthly', priority: 0.6, lastmod: '2025-05-26' },
  ],
}
