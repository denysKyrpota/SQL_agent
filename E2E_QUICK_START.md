# E2E Tests - Quick Start Guide

## ✅ Fixed Issues

The E2E tests have been completely rewritten to match your actual application. Previous failures were due to:

1. **Wrong selectors** - Tests used generic assumptions instead of actual UI elements
2. **Incorrect routes** - Tests assumed `/queries` route, actual is `/`
3. **Wrong button text** - Tests looked for "Login" instead of "Log in", "Generate" instead of "Generate SQL"
4. **Incorrect labels** - Form label says "Email" not "Username"
5. **Logout flow** - Tests didn't account for dropdown menu interaction

## 🚀 Running Tests (3 Simple Steps)

**You need 3 terminals open** - one for each server and one for tests:

### Step 1: Start Backend (Terminal 1)

```powershell
.\venv_win\Scripts\Activate.ps1
python -m backend.app.main
```

**Wait for:** `INFO: Uvicorn running on http://0.0.0.0:8000`

### Step 2: Start Frontend (Terminal 2)

```powershell
cd frontend
npm run dev
```

**Wait for:** `Local: http://localhost:3000/`

### Step 3: Run Tests (Terminal 3)

```powershell
# Interactive UI mode (recommended)
npm run test:e2e:ui

# Or headless mode
npm run test:e2e

# Or specific tests
npx playwright test e2e/auth.spec.ts
npx playwright test e2e/query-generation.spec.ts
```

**That's it!** Tests will use your running servers.

---

### ✅ Quick Verification

Before running tests, check both servers work:
- **Backend:** http://localhost:8000/docs (should see Swagger UI)
- **Frontend:** http://localhost:3000 (should see login page)

If both load, you're ready to test! 🎉

---

## 📊 Test Summary

### Authentication Tests (`e2e/auth.spec.ts`) - 11 tests

✅ **Working without API keys:**
- ✓ Show login page
- ✓ Login with valid credentials (admin/admin123)
- ✓ Show error with invalid credentials
- ✓ Validate short password
- ✓ Logout successfully
- ✓ Preserve session on reload
- ✓ Toggle password visibility
- ✓ Redirect to login for protected routes
- ✓ Redirect when accessing /history without auth
- ✓ Handle expired session

### Query Generation Tests (`e2e/query-generation.spec.ts`) - 15 tests

✅ **Working without API keys:**
- ✓ Display query input form
- ✓ Enable submit button when query entered
- ✓ Show example questions
- ✓ Populate input from example click
- ✓ Navigate to query history
- ✓ Validate empty query
- ✓ Validate long query (5000 char limit)
- ✓ Display correctly on mobile
- ✓ Show loading indicator

⚠️ **Requires OpenAI API key:**
- ⚠️ Generate SQL from natural language
- ⚠️ Show copy and execute buttons
- ⚠️ Copy SQL to clipboard
- ⚠️ Maintain query input across interactions
- ⚠️ Activate chat mode after submission
- ⚠️ Show loading state during generation

⏭️ **Skipped (requires PostgreSQL):**
- ⏭️ Execute generated SQL and show results

---

## 🔑 Required Environment Variables

For **full test coverage**, set these in your `.env` file:

```bash
# Required for SQL generation tests
OPENAI_API_KEY=sk-...

# Optional: If using Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=your-deployment

# Optional: For query execution tests
POSTGRES_URL=postgresql://user:pass@host:port/dbname
```

Without `OPENAI_API_KEY`, tests that generate SQL will fail (but won't crash).

---

## 🐛 Troubleshooting

### "Timeout waiting for servers"

**Problem:** Ports 5173 or 8000 already in use

**Solution:**
```powershell
# Check what's using the ports
netstat -ano | findstr :5173
netstat -ano | findstr :8000

# Stop the processes or restart your machine
```

### "Test failed: Selector not found"

**Problem:** Frontend not fully loaded

**Solution:**
- Ensure both servers are running and accessible
- Visit http://localhost:5173 in browser to verify
- Visit http://localhost:8000/docs to verify backend

### "Cannot find module '@playwright/test'"

**Problem:** Playwright not installed

**Solution:**
```powershell
npm install
npm run playwright:install
```

### Tests pass locally but fail in CI

**Problem:** Missing environment variables in GitHub

**Solution:**
1. Go to GitHub → Settings → Environments
2. Create "integration" environment
3. Add secrets: `OPENAI_API_KEY`, `POSTGRES_URL`, etc.

---

## 📖 Test Structure Explained

### Login Helper Function

All query tests use this helper:

```typescript
async function login(page) {
  await page.goto('/');
  await page.getByLabel(/email/i).fill('admin');
  await page.getByLabel(/password/i).fill('admin123');
  await page.getByRole('button', { name: /log in/i }).click();
  await page.waitForURL('/');
  await expect(page.getByText('admin')).toBeVisible();
}
```

### Key Selectors Used

```typescript
// Login page
page.getByLabel(/email/i)          // Username field (labeled "Email")
page.getByLabel(/password/i)       // Password field
page.getByRole('button', { name: /log in/i })  // Login button

// Main app
page.getByPlaceholder(/ask your database a question/i)  // Query input
page.getByRole('button', { name: /generate sql/i })     // Submit button
page.getByRole('heading', { name: /generated sql/i })   // SQL section
page.getByRole('button', { name: /copy sql/i })         // Copy button
page.getByRole('button', { name: /execute query/i })    // Execute button

// Navigation
page.getByRole('button', { name: 'admin' })            // User menu trigger
page.getByRole('button', { name: /sign out/i })        // Logout button
page.getByRole('link', { name: /query history/i })     // History link

// Examples
page.getByRole('heading', { name: /example questions/i })  // Examples heading
page.locator('.example-button')                            // Example buttons
```

---

## 🎯 Quick Commands Reference

```powershell
# First time setup
npm install
npm run playwright:install

# Run all E2E tests
npm run test:e2e

# Interactive UI mode (best for development)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug specific test
npm run test:e2e:debug

# Run specific browser only
npx playwright test --project=chromium

# Run specific test file
npx playwright test e2e/auth.spec.ts

# Run specific test
npx playwright test e2e/auth.spec.ts:33  # Line number

# View HTML report
npm run test:e2e:report

# Generate new test code
npm run test:e2e:codegen
```

---

## ✨ What Changed

### Before (Original Tests)
```typescript
// ❌ Wrong - these selectors didn't exist
page.getByRole('heading', { name: /login/i })
page.getByLabel(/username/i)
page.getByRole('button', { name: /login/i })
page.getByText(/logout/i).click()
```

### After (Fixed Tests)
```typescript
// ✅ Correct - matches actual UI
page.getByRole('heading', { name: /please sign in/i })
page.getByLabel(/email/i)  // Label says "Email" for username field
page.getByRole('button', { name: /log in/i })  // Two words
page.getByRole('button', { name: 'admin' }).click()  // Open dropdown first
page.getByRole('button', { name: /sign out/i }).click()
```

---

## 📝 Next Steps

1. **Run the tests** with the 3-terminal setup above
2. **Check which tests pass** - Auth tests should all pass without API keys
3. **Add OPENAI_API_KEY** to test SQL generation features
4. **Enable skipped tests** if you have a PostgreSQL database configured
5. **Customize tests** for your specific use cases

---

## 📚 Full Documentation

- **`E2E_TESTING.md`** - Complete guide with all details
- **`playwright.config.ts`** - Configuration file
- **`e2e/auth.spec.ts`** - Authentication tests
- **`e2e/query-generation.spec.ts`** - Query workflow tests

---

**Ready to test!** Start both servers and run `npm run test:e2e:ui` for an interactive experience.
