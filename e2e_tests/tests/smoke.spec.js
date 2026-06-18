const { test, expect } = require('@playwright/test');

test('smoke test: application loads', async ({ page }) => {
  await page.goto('/');
  // Basic sanity check to ensure the React app mounted
  await expect(page).toHaveTitle(/ReelForge/);
});
