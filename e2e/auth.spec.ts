import { test, expect } from '@playwright/test';

/**
 * Authentication E2E Tests
 *
 * Tests the complete authentication flow including login, logout,
 * and session persistence.
 */

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should show login page when not authenticated', async ({ page }) => {
    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Should see login form with "Please Sign In" heading
    await expect(page.getByRole('heading', { name: /please sign in/i })).toBeVisible();

    // Should see Email and Password labels
    await expect(page.getByText('Email', { exact: true })).toBeVisible();
    await expect(page.getByText('Password', { exact: true })).toBeVisible();

    // Should see login button
    await expect(page.getByRole('button', { name: /log in/i })).toBeVisible();

    // Should see demo credentials
    await expect(page.getByText(/demo credentials/i)).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    // Fill login form (label says "Email" but it's the username field)
    await page.getByLabel(/email/i).fill('admin');
    await page.locator('input[type="password"]').fill('admin123');

    // Click login button
    await page.getByRole('button', { name: /log in/i }).click();

    // Should redirect to main app (root path)
    await expect(page).toHaveURL('/');

    // Should show user interface - wait for the header with username
    await expect(page.getByText('admin')).toBeVisible({ timeout: 10000 });

    // Should show the query input placeholder
    await expect(page.getByPlaceholder(/ask your database a question/i)).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    // Fill login form with invalid credentials
    await page.getByLabel(/email/i).fill('invalid');
    await page.locator('input[type="password"]').fill('wrongpassword12345');

    // Click login button
    await page.getByRole('button', { name: /log in/i }).click();

    // Should show error message
    await expect(page.getByRole('alert')).toBeVisible();

    // Should remain on login page
    await expect(page).toHaveURL(/.*login/);
  });

  test('should show validation error for short password', async ({ page }) => {
    // Fill login form with short password
    await page.getByLabel(/email/i).fill('admin');
    await page.locator('input[type="password"]').fill('short');

    // Click login button
    await page.getByRole('button', { name: /log in/i }).click();

    // Should show validation error (frontend validation)
    await expect(page.getByText(/password must be at least 8 characters/i)).toBeVisible();

    // Should remain on login page
    await expect(page).toHaveURL(/.*login/);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.getByLabel(/email/i).fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: /log in/i }).click();

    // Wait for redirect to main app
    await page.waitForURL('/');
    await expect(page.getByText('admin')).toBeVisible();

    // Click on username to open dropdown menu
    await page.getByRole('button', { name: 'admin' }).click();

    // Click "Sign out" in the dropdown
    await page.getByRole('button', { name: /sign out/i }).click();

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);
    await expect(page.getByRole('heading', { name: /please sign in/i })).toBeVisible();
  });

  test('should preserve session on page reload', async ({ page }) => {
    // Login
    await page.getByLabel(/email/i).fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: /log in/i }).click();
    await page.waitForURL('/');

    // Verify logged in
    await expect(page.getByText('admin')).toBeVisible();

    // Reload page
    await page.reload();

    // Should still be authenticated
    await expect(page.getByText('admin')).toBeVisible();
    await expect(page).toHaveURL('/');
  });

  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.locator('input[type="password"]');
    const toggleButton = page.getByRole('button', { name: /show password|hide password/i });

    // Password should be hidden by default
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Click toggle to show password
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // Click toggle to hide password again
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });
});

test.describe('Authentication Security', () => {
  test('should redirect to login for protected routes when not authenticated', async ({ page }) => {
    // Try to access protected route directly
    await page.goto('/');

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);
    await expect(page.getByRole('heading', { name: /please sign in/i })).toBeVisible();
  });

  test('should redirect to login when accessing history without auth', async ({ page }) => {
    // Try to access history page
    await page.goto('/history');

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);
  });

  test('should handle expired session gracefully', async ({ page, context }) => {
    // Login first
    await page.goto('/');
    await page.getByLabel(/email/i).fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: /log in/i }).click();
    await page.waitForURL('/');

    // Clear cookies to simulate expired session
    await context.clearCookies();

    // Try to navigate or reload
    await page.reload();

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);
  });
});
