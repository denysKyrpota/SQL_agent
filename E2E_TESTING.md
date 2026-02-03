# E2E Testing Guide

This guide explains how to run end-to-end (E2E) tests using Playwright.

## Quick Start

### Prerequisites

1. **Backend dependencies installed** (Python packages):
   ```bash
   pip install -r requirements.txt
   ```

2. **Frontend dependencies installed**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Root dependencies installed** (Playwright):
   ```bash
   npm install
   ```

4. **Playwright browsers installed** (first time only):
   ```bash
   npm run playwright:install
   ```

5. **Database initialized**:
   ```bash
   # Windows PowerShell
   .\venv_win\Scripts\python.exe scripts\init_db.py

   # Linux/Mac
   python scripts/init_db.py
   ```

---

## Running E2E Tests Locally

Playwright can automatically start servers, or you can start them manually for faster repeated runs.

### Option 1: Automatic Server Management (Easiest)

Just run the tests - Playwright starts everything:

```bash
npm run test:e2e
```

If servers are already running, Playwright will reuse them automatically (faster).

### Option 2: Manual Server Management (Faster for Development)

**Terminal 1 - Backend Server:**
```bash
# Windows PowerShell
.\venv_win\Scripts\Activate.ps1
python -m backend.app.main

# Linux/Mac
source venv/bin/activate
python -m backend.app.main
```

**Terminal 2 - Frontend Server:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Run E2E Tests:**
```bash
# Run all tests
npm run test:e2e

# Run with UI mode (interactive)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug specific test
npm run test:e2e:debug

# View last HTML report
npm run test:e2e:report
```

### Option 2: PowerShell Helper Script (Windows)

Use the provided PowerShell script for a guided experience:

---

## Running E2E Tests in CI

In CI environments, Playwright automatically starts and stops the servers. No manual setup needed.

The GitHub Actions workflow (`.github/workflows/pull-request.yml`) handles:
- Installing dependencies
- Setting up database
- Starting servers
- Running tests across 5 browser configurations
- Generating reports

---

## Test Structure

### Test Files

- **`e2e/auth.spec.ts`** - Authentication flow tests (11 tests)
  - Login page display
  - Login with valid/invalid credentials
  - Password validation
  - Logout functionality
  - Session persistence
  - Password visibility toggle
  - Protected routes
  - Expired sessions

- **`e2e/query-generation.spec.ts`** - SQL generation workflow (15 tests)
  - Query input form validation
  - Natural language to SQL conversion
  - Copy and Execute buttons
  - Clipboard operations
  - Example questions interaction
  - Chat mode activation
  - Query history navigation
  - Error handling
  - Responsive layout
  - Loading states

**Total: 26 E2E tests covering critical user journeys**

**Note:** Some tests require OpenAI API key for SQL generation. Tests that require database execution are skipped by default.

### Browser Coverage

Tests run across 5 configurations:
- Desktop Chrome (Chromium)
- Desktop Firefox
- Desktop Safari (WebKit)
- Mobile Chrome (Pixel 5)
- Mobile Safari (iPhone 12)

---

## Configuration

### playwright.config.ts

Key configuration options:

```typescript
{
  testDir: './e2e',                    // Test directory
  timeout: 30000,                       // 30s per test
  retries: process.env.CI ? 2 : 0,     // Retry on CI
  workers: process.env.CI ? 1 : undefined, // Parallel execution
  baseURL: 'http://localhost:3000',    // Frontend URL
}
```

### Environment Variables

- **`PLAYWRIGHT_BASE_URL`** - Override frontend URL (default: `http://localhost:3000`)
- **`CI`** - Set to `true` to enable automatic server management

---

## Test Output

### Reports

After running tests, reports are generated in:

- **`playwright-report/`** - HTML report (view with `npm run test:e2e:report`)
- **`playwright-report/results.json`** - JSON results
- **`playwright-report/results.xml`** - JUnit XML for CI
- **`test-results/`** - Screenshots, videos, traces for failed tests

### Viewing Results

```bash
# Open HTML report
npm run test:e2e:report

# Or directly
npx playwright show-report playwright-report
```

---

## Writing New Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: Navigate, login, etc.
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    const button = page.getByRole('button', { name: /submit/i });

    // Act
    await button.click();

    // Assert
    await expect(page.getByText(/success/i)).toBeVisible();
  });
});
```

### Best Practices

1. **Use semantic locators:**
   ```typescript
   // Good
   page.getByRole('button', { name: /login/i })
   page.getByLabel(/username/i)

   // Avoid
   page.locator('.btn-primary')
   page.locator('#username-input')
   ```

2. **Wait for elements properly:**
   ```typescript
   // Good
   await expect(element).toBeVisible();
   await page.waitForSelector('table');

   // Avoid
   await page.waitForTimeout(5000); // Flaky
   ```

3. **Clean up state:**
   ```typescript
   test.afterEach(async ({ context }) => {
     // Clear cookies/storage if needed
     await context.clearCookies();
   });
   ```

---

## Debugging Tests

### Interactive UI Mode

```bash
npm run test:e2e:ui
```

Features:
- See test execution in real-time
- Inspect DOM at each step
- Time travel through test steps
- Edit and re-run tests

### Debug Mode

```bash
npm run test:e2e:debug
```

Features:
- Tests run in headed mode with DevTools open
- Execution pauses at breakpoints
- Can step through test code

### Playwright Inspector

```bash
npx playwright test --debug
```

### Generate Tests with Codegen

```bash
npm run test:e2e:codegen
```

Opens a browser where you can interact with your app and Playwright generates test code automatically.

---

## Troubleshooting

### Issue: "Timeout waiting for servers"

**Cause:** Servers not starting or ports already in use

**Solution:**
1. Check if ports 5173 (frontend) and 8000 (backend) are available:
   ```bash
   # Windows
   netstat -ano | findstr :5173
   netstat -ano | findstr :8000

   # Linux/Mac
   lsof -i :5173
   lsof -i :8000
   ```

2. Kill processes if needed
3. Start servers manually (see Option 1 above)

### Issue: "Test failed with timeout"

**Cause:** Selector not found or element not interactive

**Solution:**
1. Run with `--headed` to see what's happening:
   ```bash
   npm run test:e2e:headed
   ```

2. Check the screenshot in `test-results/`
3. Use UI mode for interactive debugging:
   ```bash
   npm run test:e2e:ui
   ```

### Issue: "Cannot find module '@playwright/test'"

**Cause:** Playwright not installed

**Solution:**
```bash
npm install
npm run playwright:install
```

### Issue: "Database not found"

**Cause:** Database not initialized

**Solution:**
```bash
# Windows
.\venv_win\Scripts\python.exe scripts\init_db.py

# Linux/Mac
python scripts/init_db.py
```

---

## CI/CD Integration

### GitHub Actions

The workflow automatically:
1. Installs all dependencies
2. Installs Playwright browsers with system dependencies
3. Initializes test database
4. Builds frontend
5. Runs E2E tests across all browsers
6. Uploads artifacts (reports, screenshots, videos)

### Environment Setup

Required secrets in GitHub (Environment: `integration`):
- `OPENAI_API_KEY` - For SQL generation
- `POSTGRES_URL` - For database queries
- `AZURE_OPENAI_*` - Optional, if using Azure OpenAI

---

## Performance Tips

### Faster Test Execution

1. **Run specific browser only:**
   ```bash
   npx playwright test --project=chromium
   ```

2. **Run specific test file:**
   ```bash
   npx playwright test e2e/auth.spec.ts
   ```

3. **Run in parallel (locally):**
   ```bash
   npx playwright test --workers=4
   ```

4. **Skip slow tests:**
   ```typescript
   test('slow test', async ({ page }) => {
     test.slow(); // Triples timeout
     // ...
   });
   ```

---

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [Test Generator](https://playwright.dev/docs/codegen)

---

## Summary

**For local development:**
1. Start backend: `python -m backend.app.main`
2. Start frontend: `cd frontend && npm run dev`
3. Run tests: `npm run test:e2e`

**For CI/CD:**
- Everything is automated in `.github/workflows/pull-request.yml`
- Tests run on every pull request
- Results posted as PR comment
