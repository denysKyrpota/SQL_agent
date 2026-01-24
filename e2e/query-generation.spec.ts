import { test, expect } from '@playwright/test';

/**
 * SQL Query Generation E2E Tests
 *
 * Tests the complete SQL generation workflow including:
 * - Natural language input
 * - SQL generation
 * - Query execution
 * - Results display
 * - CSV export
 *
 * Note: These tests require OpenAI API key to be configured
 */

// Helper function to login
async function login(page) {
  await page.goto('/');
  await page.getByLabel(/email/i).fill('admin');
  await page.locator('#password').fill('admin123');
  await page.getByRole('button', { name: /log in/i }).click();
  await page.waitForURL('/');
  await expect(page.getByText('admin', { exact: true })).toBeVisible();
}

test.describe('Query Generation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display query input form on main page', async ({ page }) => {
    // Should show the query input placeholder
    const queryInput = page.getByPlaceholder(/ask your database a question/i);
    await expect(queryInput).toBeVisible();

    // Should show Generate SQL button
    await expect(page.getByRole('button', { name: /generate sql/i })).toBeVisible();

    // Button should be disabled when input is empty
    await expect(page.getByRole('button', { name: /generate sql/i })).toBeDisabled();
  });

  test('should enable submit button when query is entered', async ({ page }) => {
    const queryInput = page.getByPlaceholder(/ask your database a question/i);
    const submitButton = page.getByRole('button', { name: /generate sql/i });

    // Button disabled initially
    await expect(submitButton).toBeDisabled();

    // Type query
    await queryInput.fill('Show me all users');

    // Button should be enabled
    await expect(submitButton).toBeEnabled();
  });

  test('should generate SQL from natural language', async ({ page }) => {
    // Enter natural language query
    const queryInput = page.getByPlaceholder(/ask your database a question/i);
    await queryInput.fill('Show me all users');

    // Submit query
    await page.getByRole('button', { name: /generate sql/i }).click();

    // Wait for SQL generation (this calls OpenAI API)
    // The app uses chat-based UI - SQL appears in message bubbles with "SQL Query" label
    await expect(page.getByText('SQL Query', { exact: true })).toBeVisible({ timeout: 30000 });

    // Should display SQL in a code block within the message
    const sqlContent = page.locator('pre code');
    await expect(sqlContent).toBeVisible();

    // SQL should contain SELECT keyword
    const text = await sqlContent.textContent();
    expect(text?.toUpperCase()).toContain('SELECT');
  });

  test('should show copy and execute buttons after SQL generation', async ({ page }) => {
    // Generate SQL
    await page.getByPlaceholder(/ask your database a question/i).fill('Show me 5 users');
    await page.getByRole('button', { name: /generate sql/i }).click();

    // Wait for SQL to be generated (chat-based UI shows "SQL Query" label)
    await expect(page.getByText('SQL Query', { exact: true })).toBeVisible({ timeout: 30000 });

    // Should show Copy SQL button
    await expect(page.getByRole('button', { name: /copy sql/i })).toBeVisible();

    // Should show Execute Query button
    await expect(page.getByRole('button', { name: /execute query/i })).toBeVisible();
  });

  test.skip('should execute generated SQL and show results', async ({ page }) => {
    // This test is skipped because it requires a working PostgreSQL connection
    // Enable this test when testing against a real database

    // Generate SQL
    await page.getByPlaceholder(/ask your database a question/i).fill('Show me 10 users');
    await page.getByRole('button', { name: /generate sql/i }).click();
    await expect(page.getByText('SQL Query', { exact: true })).toBeVisible({ timeout: 30000 });

    // Execute query
    await page.getByRole('button', { name: /execute query/i }).click();

    // Wait for results
    await expect(page.getByRole('heading', { name: /query results/i })).toBeVisible({ timeout: 15000 });

    // Should show results table
    await expect(page.getByRole('table')).toBeVisible();

    // Should show Export CSV button
    await expect(page.getByRole('button', { name: /export csv/i })).toBeVisible();
  });

  test('should copy SQL to clipboard', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Generate SQL
    await page.getByPlaceholder(/ask your database a question/i).fill('Show me all users');
    await page.getByRole('button', { name: /generate sql/i }).click();
    await expect(page.getByText('SQL Query', { exact: true })).toBeVisible({ timeout: 30000 });

    // Click copy button
    await page.getByRole('button', { name: /copy sql/i }).click();

    // Verify clipboard contains SQL (check for SELECT keyword)
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardText.toUpperCase()).toContain('SELECT');
  });

  test('should switch to chat mode and show user message after generation', async ({ page }) => {
    const queryInput = page.getByPlaceholder(/ask your database a question/i);

    // Enter text
    const testQuery = 'Show me all users from last month';
    await queryInput.fill(testQuery);

    // Verify the text is there before submission
    await expect(queryInput).toHaveValue(testQuery);

    // Generate SQL
    await page.getByRole('button', { name: /generate sql/i }).click();
    await expect(page.getByText('SQL Query', { exact: true })).toBeVisible({ timeout: 30000 });

    // After submission, UI switches to chat mode - the centered input disappears
    // and the user's message should appear in the chat
    await expect(page.getByText(testQuery)).toBeVisible();
  });
});

test.describe('Example Questions', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should show example questions on initial load', async ({ page }) => {
    // Should display "Example Questions" heading
    await expect(page.getByRole('heading', { name: /example questions/i })).toBeVisible();

    // Should have at least one example button
    const exampleButtons = page.locator('.example-button');
    await expect(exampleButtons.first()).toBeVisible();
  });

  test('should populate input when example question is clicked', async ({ page }) => {
    const queryInput = page.getByPlaceholder(/ask your database a question/i);

    // Find and click first example question
    const firstExample = page.locator('.example-button').first();
    const exampleText = await firstExample.locator('.example-text').textContent();

    await firstExample.click();

    // Query input should be filled with example text
    await expect(queryInput).toHaveValue(exampleText || '');

    // Generate SQL button should be enabled
    await expect(page.getByRole('button', { name: /generate sql/i })).toBeEnabled();
  });
});

test.describe('Chat Conversation Mode', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should activate chat mode after first submission', async ({ page }) => {
    // Submit first query
    await page.getByPlaceholder(/ask your database a question/i).fill('Show me all users');
    await page.getByRole('button', { name: /generate sql/i }).click();

    // Wait for SQL generation (chat-based UI shows "SQL Query" label)
    await expect(page.getByText('SQL Query', { exact: true })).toBeVisible({ timeout: 30000 });

    // Chat panel should be visible (check for conversation UI elements)
    // The UI switches to chat mode with message bubbles
    const messages = page.locator('[class*="message"]');
    await expect(messages.first()).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Query History Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should navigate to query history page', async ({ page }) => {
    // Click Query History link in the main navigation
    await page.getByRole('link', { name: /query history/i }).click();

    // Should navigate to history page
    await expect(page).toHaveURL('/history');

    // Should show query history page content
    await expect(page.getByRole('heading', { name: /query history/i })).toBeVisible();
  });
});

test.describe('Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should validate empty query', async ({ page }) => {
    const submitButton = page.getByRole('button', { name: /generate sql/i });

    // Submit button should be disabled for empty input
    await expect(submitButton).toBeDisabled();

    // Try to type spaces only
    await page.getByPlaceholder(/ask your database a question/i).fill('   ');

    // Button should still be disabled
    await expect(submitButton).toBeDisabled();
  });

  test('should show error for excessively long query', async ({ page }) => {
    const queryInput = page.getByPlaceholder(/ask your database a question/i);

    // Create a query longer than 5000 characters
    const longQuery = 'a'.repeat(5001);
    await queryInput.fill(longQuery);

    // The textarea should truncate at max length (5000 chars)
    const value = await queryInput.inputValue();
    expect(value.length).toBeLessThanOrEqual(5000);
  });
});

test.describe('Responsive Layout', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Should still show query input
    await expect(page.getByPlaceholder(/ask your database a question/i)).toBeVisible();

    // Should show Generate SQL button
    await expect(page.getByRole('button', { name: /generate sql/i })).toBeVisible();
  });
});

test.describe('Performance', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should show loading indicator during SQL generation', async ({ page, browserName }) => {
    // Skip on webkit due to timing issues
    test.skip(browserName === 'webkit', 'Skipped on webkit due to timing issues');

    // Enter query
    await page.getByPlaceholder(/ask your database a question/i).fill('Show me all users');

    // Click generate
    const generateButton = page.getByRole('button', { name: /generate sql/i });
    await generateButton.click();

    // Should show loading indicator with "Analyzing database schema..." text
    await expect(page.locator('.loading-text')).toBeVisible({ timeout: 5000 });

    // Wait for generation to complete (chat-based UI shows "SQL Query" label)
    await expect(page.getByText('SQL Query', { exact: true })).toBeVisible({ timeout: 30000 });
  });
});
