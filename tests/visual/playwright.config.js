// Visual regression for the main look (issue #70).
// Pages are served from a local build at http://127.0.0.1:4000 (python3 -m http.server
// 4000 --directory _site). Baselines live next to this file and are updated with
// `npm run visual:update` after an intended change to the look.
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: __dirname,
  snapshotPathTemplate: '{testDir}/baselines/{arg}{ext}',
  timeout: 60000,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  use: {
    baseURL: process.env.SITE_URL || 'http://127.0.0.1:4000',
    ...devices['Desktop Chrome'],
    viewport: { width: 1280, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
    reducedMotion: 'reduce',
  },
  expect: {
    toHaveScreenshot: {
      // Font rasterisation differs slightly between machines; small drifts are not defects.
      maxDiffPixelRatio: 0.02,
      threshold: 0.3,
      animations: 'disabled',
    },
  },
});
