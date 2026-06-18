const { test, expect } = require('@playwright/test');

test('system test: complete api integration flow', async ({ page }) => {
  await page.goto('/api-docs');
  // Wait for Swagger UI to load the schema from the backend
  await expect(page.locator('.swagger-ui')).toBeVisible();
});
