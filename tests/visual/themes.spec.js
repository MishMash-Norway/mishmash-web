// Front page of every published interface theme (issue #70). Themes are student
// and community work and change more often than the main look, so a diff here
// is information for the theme's author rather than a defect in the site.
const { test, expect } = require('@playwright/test');

const THEMES = ['bubbles', 'example', 'sfa', 'techy'];

for (const name of THEMES) {
  test(`theme-${name}`, async ({ page }) => {
    await page.goto(`/ui/${name}/`, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await expect(page).toHaveScreenshot(`theme-${name}.png`, {
      fullPage: false,
      mask: [page.locator('.site-footer'), page.locator('.page-about'), page.locator('canvas')],
    });
  });
}
