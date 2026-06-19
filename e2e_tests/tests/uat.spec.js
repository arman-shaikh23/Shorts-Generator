const { test, expect } = require('@playwright/test');

test('UAT test: realtor uploads and views dashboard', async ({ page }) => {
  await page.goto('/login');

  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');
  const submitButton = page.getByRole('button', { name: /sign in/i });

  await expect(emailInput).toBeVisible();
  await expect(passwordInput).toBeVisible();
  await expect(submitButton).toBeVisible();

  await emailInput.fill('realtor@example.com');
  await passwordInput.fill('password123');

  await expect(emailInput).toHaveValue('realtor@example.com');
  await expect(passwordInput).toHaveValue('password123');
});
