/* eslint-disable import/no-extraneous-dependencies */
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})
const { i18n } = require('./i18n.config')

module.exports = withBundleAnalyzer({
  output: 'standalone',
  // -----------------------------------------------------------------------
  // TODO Phase 04: Remove these ignore flags after cleaning up admin lint errors.
  // These flags are intentionally kept to avoid surfacing 100+ pre-existing
  // ESLint / TypeScript errors in src/components/admin/* that were present
  // before Phase 03. Removing them now would break the build without fixing
  // the underlying issues first.
  // See: docs/lint-cleanup-backlog.md for the full backlog and recommended actions.
  // -----------------------------------------------------------------------
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  i18n,
  poweredByHeader: false,
  trailingSlash: true,
  basePath: '',
  env: {
    BASE_URL: process.env.API_ENDPOINT,
    NEXT_PUBLIC_TURNSTILE_SITE_KEY: process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY,
  },
})
