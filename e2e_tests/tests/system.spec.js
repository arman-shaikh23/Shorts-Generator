const { test, expect } = require('@playwright/test');

test('system test: complete api integration flow', async ({ page }) => {
  await page.goto('/api-docs');
  await expect(page.getByRole('heading', { name: /api documentation/i })).toBeVisible();
  const docsFrame = page.locator('iframe[title="API Docs"]');
  await expect(docsFrame).toBeVisible();
  await expect(docsFrame).toHaveAttribute('src', /\/docs$/);
});
