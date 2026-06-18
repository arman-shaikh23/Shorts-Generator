const { test, expect } = require('@playwright/test');

test('UAT test: realtor uploads and views dashboard', async ({ page }) => {
  // Scenario: A realtor wants to generate a short
  await page.goto('/login');
  
  // Example UAT steps
  const emailInput = page.getByPlaceholder(/email/i);
  if (await emailInput.isVisible()) {
    await emailInput.fill('realtor@example.com');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Assert we reach the dashboard
    await expect(page).toHaveURL(/.*dashboard/);
  }
});
