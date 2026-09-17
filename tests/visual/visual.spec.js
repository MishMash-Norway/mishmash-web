// Screenshots of pages whose content rarely changes, so a diff means the look changed.
// The provenance footer is masked because its dates move with every edit.
const { test, expect } = require('@playwright/test');

const PAGES = [
  ['home-header', '/', 'header.page-header'],
  ['internal-brand', '/internal/brand/', null],
  ['accessibility', '/accessibility/', null],
  ['faq', '/faq/', null],
  ['privacy-nb', '/no/privacy/', null],
  ['event-meshup-23', '/events/meshup-23/', null],
  ['institution-uio', '/institutions/university-of-oslo/', null],
];

for (const [name, path, selector] of PAGES) {
  test(name, async ({ page }) => {
    await page.goto(path, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const target = selector ? page.locator(selector) : page;
    await expect(target).toHaveScreenshot(`${name}.png`, {
      fullPage: !selector,
      mask: [page.locator('.site-footer'), page.locator('.page-about')],
    });
  });
}
