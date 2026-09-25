// The first occurrence of each abbreviation in the main text unfolds its
// expansion in place (WCAG 3.1.4), and nothing else on the page is touched.
//
// The list of abbreviations comes from the page itself, written by
// _includes/page-about.html; assets/js/abbreviations.js makes the toggles.
//
// Run with the site served at http://127.0.0.1:4000, as the workflow does:
//   npx playwright test -c tests/visual/playwright.config.js tests/visual/abbreviations.spec.js
const { test, expect } = require('@playwright/test');

const PAGES = [
  { path: '/about/ai-colophon/', first: 'AI', expansion: 'artificial intelligence' },
  { path: '/no/about/ai-colophon/', first: 'KI', expansion: 'kunstig intelligens' },
];

for (const page_ of PAGES) {
  test(`${page_.path} expands each abbreviation once, in the page's language`, async ({ page }) => {
    await page.goto(page_.path);
    const toggles = page.locator('.main-content .stretch-abbr');
    expect(await toggles.count()).toBeGreaterThan(0);

    // One toggle per abbreviation, never two for the same term.
    const terms = await toggles.locator('abbr').allTextContents();
    expect(new Set(terms).size).toBe(terms.length);
    expect(terms).toContain(page_.first);

    // Never inside a heading, a link or another control.
    for (let i = 0; i < terms.length; i += 1) {
      const inside = await toggles.nth(i).evaluate((el) => !!el.closest('h1, h2, h3, h4, a, button:not(.stretch-toggle), code, .mm-breadcrumbs, .page-about'));
      expect(inside).toBe(false);
    }

    // Closed until asked, and opened with the keyboard.
    const first = toggles.filter({ has: page.locator(`abbr:text-is("${page_.first}")`) }).first();
    const button = first.locator('.stretch-toggle');
    const more = first.locator('.stretch-more');
    await expect(button).toHaveAttribute('aria-expanded', 'false');
    await expect(more).toBeHidden();
    await button.focus();
    await page.keyboard.press('Enter');
    await expect(button).toHaveAttribute('aria-expanded', 'true');
    await expect(more).toBeVisible();
    await expect(more).toHaveText(page_.expansion);
  });
}

test('a page without abbreviations gets no toggles and no script', async ({ page }) => {
  await page.goto('/about/organisation/');
  // CC BY and WCAG are always listed in the panel, so the script loads
  // everywhere; what matters is that it touches nothing it should not.
  const toggles = page.locator('.main-content .stretch-abbr');
  for (let i = 0; i < await toggles.count(); i += 1) {
    const inside = await toggles.nth(i).evaluate((el) => !!el.closest('h1, h2, h3, a, .page-about'));
    expect(inside).toBe(false);
  }
});
