// The header menus can be dismissed without moving the pointer or the focus.
//
// WCAG 1.4.13 asks that content brought up by pointer or keyboard can be
// dismissed the same way. The UiO web team found on 24 September 2026 that a
// reader who opened a header menu was left inside it: nothing closed it. The
// handler lives in _layouts/default.html.
//
// Run with the site served at http://127.0.0.1:4000, as the workflow does:
//   npx playwright test -c tests/visual/playwright.config.js tests/visual/menus.spec.js
const { test, expect } = require('@playwright/test');

const MENUS = [
  { name: 'language', selector: '.mm-nav details.lang-switcher' },
  { name: 'work packages', selector: '.mm-nav details.wp-dropdown:not(.lang-switcher)' },
];

for (const menu of MENUS) {
  test(`the ${menu.name} menu closes on Escape and gives the focus back`, async ({ page }) => {
    await page.goto('/');
    const details = page.locator(menu.selector).first();
    const summary = details.locator('> summary');

    await summary.focus();
    await page.keyboard.press('Enter');
    await expect(details).toHaveAttribute('open', '');
    await expect(summary).toHaveAttribute('aria-expanded', 'true');

    await page.keyboard.press('Escape');
    await expect(details).not.toHaveAttribute('open', '');
    await expect(summary).toHaveAttribute('aria-expanded', 'false');

    // The focus has to come back to the button, or a keyboard reader is left
    // pointing at something that is no longer on the page.
    const focused = await page.evaluate(() => document.activeElement?.tagName.toLowerCase());
    expect(focused).toBe('summary');
  });

  test(`the ${menu.name} menu closes when the reader presses elsewhere`, async ({ page }) => {
    await page.goto('/');
    const details = page.locator(menu.selector).first();
    await details.locator('> summary').click();
    await expect(details).toHaveAttribute('open', '');

    await page.locator('main, .main-content').first().click({ position: { x: 5, y: 5 } });
    await expect(details).not.toHaveAttribute('open', '');
  });
}

test('only one header menu is open at a time', async ({ page }) => {
  await page.goto('/');
  const first = page.locator(MENUS[1].selector).first();
  const second = page.locator(MENUS[0].selector).first();
  await first.locator('> summary').click();
  await expect(first).toHaveAttribute('open', '');
  await second.locator('> summary').click();
  await expect(second).toHaveAttribute('open', '');
  await expect(first).not.toHaveAttribute('open', '');
});

test('the thumbnail link in a listing is not a second stop for the keyboard', async ({ page }) => {
  await page.goto('/events/');
  const cards = page.locator('.event-item').first();
  const links = cards.locator('a[href]');
  const count = await links.count();
  expect(count).toBeGreaterThan(0);
  for (let i = 0; i < count; i += 1) {
    const link = links.nth(i);
    const hasImage = await link.locator('img').count();
    if (hasImage) {
      // The picture repeats the link beside it, so it is hidden from both the
      // tab order and the accessibility tree (2.1.1).
      await expect(link).toHaveAttribute('tabindex', '-1');
      await expect(link).toHaveAttribute('aria-hidden', 'true');
    }
  }
});
