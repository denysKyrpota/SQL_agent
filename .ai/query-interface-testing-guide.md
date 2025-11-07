# Query Interface View - Testing Guide

## Overview

This guide provides detailed instructions for testing the Query Interface View implementation. It covers manual testing procedures, automated testing setup recommendations, and expected behaviors for all features.

**Implementation Status**: ✅ Complete (Steps 1-7)
**Testing Status**: 🔄 Manual testing required, automated tests pending
**Target Coverage**: 100% of user-facing features

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Test Environment Setup](#test-environment-setup)
3. [Manual Testing Procedures](#manual-testing-procedures)
4. [Automated Testing Recommendations](#automated-testing-recommendations)
5. [API Mocking for Tests](#api-mocking-for-tests)
6. [Accessibility Testing](#accessibility-testing)
7. [Performance Testing](#performance-testing)
8. [Browser Compatibility](#browser-compatibility)
9. [Bug Reporting Template](#bug-reporting-template)

---

## Prerequisites

### Required Setup

1. **Backend API Running**:
   ```bash
   # Navigate to backend directory
   cd backend

   # Activate virtual environment
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows

   # Start FastAPI server
   uvicorn main:app --reload
   ```

2. **Frontend Development Server**:
   ```bash
   # Navigate to frontend directory
   cd frontend

   # Install dependencies (if not already done)
   npm install

   # Start development server
   npm run dev
   ```

3. **Test Database**:
   - Ensure SQLite database has sample data
   - Run initialization script if needed:
     ```bash
     python scripts/init_db.py
     ```

4. **Authentication**:
   - Have test user credentials ready
   - Ensure session-based auth is working

### Browser DevTools Setup

- Open browser DevTools (F12)
- Keep **Console** tab visible to catch errors
- Enable **Network** tab to monitor API calls
- Use **Lighthouse** for accessibility audits

---

## Test Environment Setup

### Environment Variables

Create/verify `.env` file in frontend directory:

```env
# Development
REACT_APP_API_BASE_URL=http://localhost:8000/api

# Production (when deploying)
# REACT_APP_API_BASE_URL=/api
```

### TypeScript Configuration

Verify `tsconfig.json` has path aliases configured:

```json
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "@/*": ["*"]
    }
  }
}
```

### CSS Modules Support

Ensure build tool (Vite/CRA) supports CSS Modules:
- Files ending in `.module.css` should be processed correctly
- Class names should be scoped to components

---

## Manual Testing Procedures

### 1. Query Submission Workflow

#### Test Case 1.1: Valid Query Submission

**Steps**:
1. Navigate to Query Interface View
2. Enter valid natural language query: `"Show me all orders from the last 30 days"`
3. Click "Generate SQL" button

**Expected Results**:
- ✅ Character count updates in real-time
- ✅ Loading indicator appears with "Analyzing schema..." message
- ✅ Loading indicator changes to "Generating SQL..." after ~500ms
- ✅ SQL preview section appears with generated SQL
- ✅ SQL has syntax highlighting (keywords in blue, strings in green)
- ✅ "Execute Query" and "Copy SQL" buttons are visible
- ✅ Page auto-scrolls to SQL preview section
- ✅ Input textarea is cleared on success
- ✅ No console errors

**API Call**:
```
POST http://localhost:8000/api/queries
Request Body: {
  "natural_language_query": "Show me all orders from the last 30 days"
}
```

#### Test Case 1.2: Empty Query Validation

**Steps**:
1. Leave textarea empty
2. Click "Generate SQL" button

**Expected Results**:
- ✅ Validation error appears: "Please enter a question"
- ✅ Error alert has warning icon (⚠️)
- ✅ No API call is made
- ✅ Focus returns to textarea

#### Test Case 1.3: Whitespace-Only Query

**Steps**:
1. Enter only spaces/tabs in textarea: `"     "`
2. Click "Generate SQL" button

**Expected Results**:
- ✅ Validation error: "Please enter a valid question"
- ✅ No API call made

#### Test Case 1.4: Character Limit Validation

**Steps**:
1. Enter text exceeding 5000 characters
2. Observe character count
3. Try to submit

**Expected Results**:
- ✅ Character count shows "5001/5000" (or current count)
- ✅ Character count turns red when > 5000
- ✅ Validation error: "Question exceeds 5000 character limit"
- ✅ Submit button disabled when over limit

#### Test Case 1.5: Example Question Selection

**Steps**:
1. Click on an example question: "What were our top 10 customers by revenue last quarter?"
2. Observe textarea

**Expected Results**:
- ✅ Textarea populates with example text
- ✅ Character count updates
- ✅ Cursor is placed in textarea
- ✅ Can edit the populated text
- ✅ Can submit the example query

#### Test Case 1.6: Failed SQL Generation

**Steps**:
1. Submit query that backend cannot process
2. Backend returns `status: "failed_generation"`

**Expected Results**:
- ✅ Loading indicator disappears
- ✅ Error alert appears with generation icon (🔄)
- ✅ Error message: "Unable to generate query. Try rephrasing your question."
- ✅ Recovery suggestion shown: "Try rephrasing your question or being more specific..."
- ✅ "Try Again" button visible
- ✅ Clicking "Try Again" clears error and resets form
- ✅ Original input text preserved in textarea

---

### 2. SQL Preview & Execution

#### Test Case 2.1: SQL Syntax Highlighting

**Steps**:
1. Generate SQL successfully
2. Inspect SQL preview section

**Expected Results**:
- ✅ SQL keywords (SELECT, FROM, WHERE, JOIN, etc.) highlighted in blue
- ✅ String literals ('...') highlighted in green
- ✅ Numbers highlighted in orange
- ✅ Comments (--...) highlighted in gray
- ✅ Line numbers displayed on left side
- ✅ Dark background (#1e293b) for code block
- ✅ Monospace font (Monaco, Menlo, Ubuntu Mono)
- ✅ Horizontal scroll appears for long lines

#### Test Case 2.2: Copy SQL to Clipboard

**Steps**:
1. Generate SQL successfully
2. Click "Copy SQL" button

**Expected Results**:
- ✅ Success toast appears: "SQL copied to clipboard!"
- ✅ Toast auto-dismisses after 3 seconds
- ✅ Clipboard contains full SQL text (verify with Ctrl+V)
- ✅ Clipboard text has no HTML formatting (plain text only)

#### Test Case 2.3: Execute Valid SQL

**Steps**:
1. Generate SQL successfully
2. Click "Execute Query" button

**Expected Results**:
- ✅ Loading indicator appears: "Executing query..."
- ✅ Execute button shows loading spinner
- ✅ Execute button is disabled during execution
- ✅ Results section appears after completion
- ✅ Performance metrics displayed
- ✅ Results table shows data
- ✅ Page auto-scrolls to results section
- ✅ No console errors

**API Call**:
```
POST http://localhost:8000/api/queries/1/execute
```

#### Test Case 2.4: Execute SQL with Error

**Steps**:
1. Force backend to return `status: "failed_execution"`
2. Click "Execute Query" button

**Expected Results**:
- ✅ Loading indicator disappears
- ✅ Error alert appears with execution icon (❌)
- ✅ Error message: "Query failed to execute. The generated SQL may be invalid."
- ✅ Error detail shows backend error message if available
- ✅ Recovery suggestion shown
- ✅ "Try Again" button clears error and allows retry
- ✅ SQL preview remains visible

#### Test Case 2.5: Query Timeout

**Steps**:
1. Submit query that takes > 5 minutes to execute
2. Wait for timeout

**Expected Results**:
- ✅ After 5 minutes, request is aborted
- ✅ Error alert appears with timeout icon (⏱️)
- ✅ Error message: "Query took too long to execute. Try narrowing your search."
- ✅ Recovery suggestion: "Simplify your query, add more filters, or reduce date ranges."
- ✅ Can retry or start new query

---

### 3. Results Display

#### Test Case 3.1: Performance Metrics

**Steps**:
1. Execute query successfully
2. Inspect performance metrics section

**Expected Results**:
- ✅ "Generation" time displayed in milliseconds
- ✅ "Execution" time displayed in milliseconds
- ✅ Color coding:
  - Green (< 5 seconds)
  - Yellow (5-30 seconds)
  - Red (> 30 seconds)
- ✅ Total time calculated correctly

#### Test Case 3.2: Results Table Display

**Steps**:
1. Execute query returning multiple rows and columns
2. Inspect results table

**Expected Results**:
- ✅ All columns displayed with headers
- ✅ Column headers use proper casing (snake_case converted to Title Case)
- ✅ All rows displayed (up to page size limit)
- ✅ Alternating row colors for readability
- ✅ NULL values displayed as "(null)" in gray italics
- ✅ Numbers right-aligned
- ✅ Text left-aligned
- ✅ Dates formatted properly
- ✅ Boolean values shown as "Yes"/"No" or checkmarks
- ✅ Column widths auto-adjusted based on data type:
  - ID columns: narrow (100px)
  - Numbers: medium (120px)
  - Dates: medium (150px)
  - Text: wide (200px+)

#### Test Case 3.3: Empty Result Set

**Steps**:
1. Execute query returning 0 rows

**Expected Results**:
- ✅ Results section appears
- ✅ Performance metrics shown
- ✅ Empty state message: "No results found"
- ✅ Explanation: "Your query executed successfully but returned no data."
- ✅ No table displayed
- ✅ Export button disabled or hidden

#### Test Case 3.4: Large Result Set (Horizontal Scroll)

**Steps**:
1. Execute query returning many columns (> 10)
2. Resize browser to narrow width

**Expected Results**:
- ✅ Horizontal scrollbar appears
- ✅ First column frozen on mobile (< 768px)
- ✅ All columns accessible via scroll
- ✅ Table maintains readability

---

### 4. Pagination & Export

#### Test Case 4.1: Pagination Display

**Steps**:
1. Execute query returning > 500 rows

**Expected Results**:
- ✅ Pagination controls appear below table
- ✅ Page indicator: "Page 1 of X"
- ✅ Row count: "Showing 1-500 of XXXX rows"
- ✅ "Previous" button disabled on page 1
- ✅ "Next" button enabled if more pages exist

#### Test Case 4.2: Navigate to Next Page

**Steps**:
1. Execute query with multiple pages
2. Click "Next" button

**Expected Results**:
- ✅ API call made: `GET /api/queries/1/results?page=2`
- ✅ Table updates with new rows
- ✅ Page indicator updates: "Page 2 of X"
- ✅ Row count updates: "Showing 501-1000 of XXXX rows"
- ✅ "Previous" button enabled
- ✅ Page auto-scrolls to top of results
- ✅ No page reload

#### Test Case 4.3: Navigate to Previous Page

**Steps**:
1. Navigate to page 2
2. Click "Previous" button

**Expected Results**:
- ✅ Returns to page 1
- ✅ Shows rows 1-500
- ✅ "Previous" button disabled again
- ✅ Auto-scroll to results

#### Test Case 4.4: Pagination on Last Page

**Steps**:
1. Navigate to last page of results

**Expected Results**:
- ✅ "Next" button disabled
- ✅ Row count accurate: "Showing X-Y of Y rows"
- ✅ Partial page displayed correctly (e.g., 501-523 if only 523 total)

#### Test Case 4.5: CSV Export (Small Dataset)

**Steps**:
1. Execute query returning < 10,000 rows
2. Click "Export CSV" button

**Expected Results**:
- ✅ CSV file downloads immediately
- ✅ Filename format: `query_1_1730822400000.csv` (query_id_timestamp.csv)
- ✅ Success toast: "CSV exported successfully!"
- ✅ CSV contains all rows (not just current page)
- ✅ CSV has proper headers
- ✅ CSV values properly escaped (quotes, commas)

**API Call**:
```
GET http://localhost:8000/api/queries/1/export
```

#### Test Case 4.6: CSV Export (Large Dataset)

**Steps**:
1. Execute query returning > 10,000 rows
2. Click "Export CSV" button

**Expected Results**:
- ✅ Warning message appears (if implemented)
- ✅ CSV downloads with max 10,000 rows
- ✅ OR 413 error received: "Results are too large to export (max 10,000 rows)."
- ✅ Error toast displays appropriate message

---

### 5. Error Handling

#### Test Case 5.1: Network Error (Offline)

**Steps**:
1. Disconnect from network
2. Submit query

**Expected Results**:
- ✅ Error alert with network icon (🌐)
- ✅ Error message: "Network error. Please check your connection."
- ✅ Recovery suggestion: "Check your internet connection and try again."
- ✅ "Try Again" button available

#### Test Case 5.2: Session Expiration (401)

**Steps**:
1. Manually clear session cookie or wait for expiration
2. Submit query or execute SQL

**Expected Results**:
- ✅ Automatic redirect to `/login`
- ✅ SessionStorage cleared
- ✅ LocalStorage cleared
- ✅ Console log: APIError with status 401

#### Test Case 5.3: Rate Limiting (429)

**Steps**:
1. Submit many requests rapidly to trigger rate limiting
2. Observe response

**Expected Results**:
- ✅ Error alert appears
- ✅ Error message: "Too many requests. Please wait a moment and try again."
- ✅ Network error type assigned
- ✅ Recovery suggestion provided

#### Test Case 5.4: Service Unavailable (503)

**Steps**:
1. Stop backend server
2. Submit query

**Expected Results**:
- ✅ Error alert appears
- ✅ Error message: "Service temporarily unavailable. Please try again."
- ✅ Network error type
- ✅ Recovery suggestion

#### Test Case 5.5: React Component Crash

**Steps**:
1. Force a React component error (modify code to throw error in render)

**Expected Results**:
- ✅ ErrorBoundary catches error
- ✅ Fallback UI displayed: "Something went wrong"
- ✅ "Refresh Page" button visible
- ✅ Error logged to console
- ✅ Rest of app remains functional (if boundary is scoped)

#### Test Case 5.6: Dismiss Error Alert

**Steps**:
1. Trigger any error
2. Click "×" dismiss button

**Expected Results**:
- ✅ Error alert disappears
- ✅ Form returns to ready state
- ✅ Can submit new query

---

### 6. User Experience Features

#### Test Case 6.1: Auto-Scroll Behavior

**Steps**:
1. Submit query (scroll position at top)
2. Wait for SQL generation
3. Execute query
4. Navigate to page 2

**Expected Results**:
- ✅ After SQL generation: scrolls to SQL preview section
- ✅ After execution: scrolls to results section
- ✅ After page change: scrolls to top of results
- ✅ Smooth scrolling animation (not instant jump)

#### Test Case 6.2: Loading States

**Steps**:
1. Observe UI during async operations

**Expected Results**:
- ✅ Submit button disabled during generation
- ✅ Execute button disabled during execution
- ✅ Loading spinners visible on buttons
- ✅ Stage-specific loading messages:
  - "Analyzing database schema..."
  - "Generating SQL query..."
  - "Executing query..."
- ✅ Loading indicator has animated spinner

#### Test Case 6.3: Input Persistence

**Steps**:
1. Type query in textarea: "test query"
2. Refresh page (F5)
3. Observe textarea

**Expected Results**:
- ✅ Input text restored from sessionStorage
- ✅ Character count updated
- ✅ After successful submission, sessionStorage cleared

#### Test Case 6.4: Keyboard Shortcuts

**Steps**:
1. Focus textarea
2. Press `Ctrl+Enter` (or `Cmd+Enter` on Mac)

**Expected Results**:
- ✅ Form submits (if implemented)
- ✅ OR no action if not implemented (future feature)

---

### 7. Responsive Design

#### Test Case 7.1: Mobile View (< 768px)

**Steps**:
1. Resize browser to 375px width (iPhone size)
2. Test all features

**Expected Results**:
- ✅ Single column layout
- ✅ Full-width buttons
- ✅ Stacked form elements
- ✅ Example questions in vertical list
- ✅ First table column frozen during horizontal scroll
- ✅ Toast notifications at bottom of screen
- ✅ Touch targets ≥ 44px height
- ✅ Text remains readable (no tiny fonts)
- ✅ All features functional

#### Test Case 7.2: Tablet View (768px - 1024px)

**Steps**:
1. Resize browser to 768px width
2. Test all features

**Expected Results**:
- ✅ Optimized spacing
- ✅ 2-column example questions
- ✅ Table shows multiple columns without scroll
- ✅ Buttons appropriately sized
- ✅ All features functional

#### Test Case 7.3: Desktop View (> 1024px)

**Steps**:
1. Resize browser to 1280px width
2. Test all features

**Expected Results**:
- ✅ Full layout with proper spacing
- ✅ Multi-column displays
- ✅ Table shows all columns comfortably
- ✅ Optimal reading width (max 1200px container)
- ✅ All features functional

---

## Automated Testing Recommendations

### Testing Stack

```bash
# Install testing dependencies
npm install --save-dev \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  vitest \
  jsdom \
  msw
```

### Unit Tests

#### Example: Button Component Test

```typescript
// components/Button/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Button from './index';

describe('Button Component', () => {
  it('renders with children', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    fireEvent.click(screen.getByText('Click Me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('disables button when loading', () => {
    render(<Button loading>Click Me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('applies variant classes', () => {
    const { container } = render(<Button variant="danger">Delete</Button>);
    expect(container.firstChild).toHaveClass('btn-danger');
  });
});
```

#### Example: Validation Utility Test

```typescript
// views/QueryInterfaceView/utils/validation.test.ts
import { describe, it, expect } from 'vitest';
import { validateQuery } from './validation';

describe('validateQuery', () => {
  it('returns null for valid query', () => {
    expect(validateQuery('What is the total sales?')).toBeNull();
  });

  it('returns error for empty query', () => {
    expect(validateQuery('')).toBe('Please enter a question');
  });

  it('returns error for whitespace-only query', () => {
    expect(validateQuery('   ')).toBe('Please enter a valid question');
  });

  it('returns error for query exceeding 5000 chars', () => {
    const longQuery = 'a'.repeat(5001);
    expect(validateQuery(longQuery)).toBe('Question exceeds 5000 character limit');
  });
});
```

### Integration Tests

#### Example: Query Submission Flow

```typescript
// views/QueryInterfaceView/QueryInterfaceView.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import QueryInterfaceView from './index';

// Mock API server
const server = setupServer(
  rest.post('/api/queries', (req, res, ctx) => {
    return res(ctx.json({
      id: 1,
      natural_language_query: 'test query',
      generated_sql: 'SELECT * FROM users',
      status: 'generated',
      generation_ms: 1234,
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('QueryInterfaceView', () => {
  it('submits query and displays SQL preview', async () => {
    const user = userEvent.setup();
    render(<QueryInterfaceView />);

    // Enter query
    const textarea = screen.getByLabelText(/enter your question/i);
    await user.type(textarea, 'Show me all users');

    // Submit
    const submitButton = screen.getByText('Generate SQL');
    await user.click(submitButton);

    // Wait for loading
    expect(screen.getByText(/analyzing schema/i)).toBeInTheDocument();

    // Wait for SQL preview
    await waitFor(() => {
      expect(screen.getByText(/SELECT \* FROM users/i)).toBeInTheDocument();
    });

    // Verify execute button appears
    expect(screen.getByText('Execute Query')).toBeInTheDocument();
  });

  it('displays validation error for empty query', async () => {
    const user = userEvent.setup();
    render(<QueryInterfaceView />);

    // Submit without entering text
    const submitButton = screen.getByText('Generate SQL');
    await user.click(submitButton);

    // Verify error
    expect(screen.getByText('Please enter a question')).toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    server.use(
      rest.post('/api/queries', (req, res, ctx) => {
        return res(ctx.status(503), ctx.json({ detail: 'Service unavailable' }));
      })
    );

    const user = userEvent.setup();
    render(<QueryInterfaceView />);

    await user.type(screen.getByLabelText(/enter your question/i), 'test');
    await user.click(screen.getByText('Generate SQL'));

    await waitFor(() => {
      expect(screen.getByText(/service temporarily unavailable/i)).toBeInTheDocument();
    });
  });
});
```

### Component Tests Coverage Goals

| Component | Coverage Target |
|-----------|-----------------|
| Button | 100% |
| TextArea | 100% |
| Toast | 100% |
| Pagination | 100% |
| QueryForm | 95% |
| SqlPreview | 90% |
| ResultsTable | 90% |
| ErrorAlert | 95% |
| QueryInterfaceView | 85% |

---

## API Mocking for Tests

### MSW (Mock Service Worker) Setup

```typescript
// mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  // Successful query creation
  rest.post('/api/queries', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: 1,
        natural_language_query: 'test query',
        generated_sql: 'SELECT * FROM users LIMIT 10',
        status: 'generated',
        generation_ms: 1234,
        created_at: new Date().toISOString(),
      })
    );
  }),

  // Successful query execution
  rest.post('/api/queries/:id/execute', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: 1,
        status: 'success',
        execution_ms: 567,
        results: {
          columns: ['id', 'name', 'email'],
          rows: [
            [1, 'John Doe', 'john@example.com'],
            [2, 'Jane Smith', 'jane@example.com'],
          ],
          total_rows: 2,
          page_size: 500,
          page_count: 1,
        },
      })
    );
  }),

  // Paginated results
  rest.get('/api/queries/:id/results', (req, res, ctx) => {
    const page = req.url.searchParams.get('page') || '1';
    return res(
      ctx.status(200),
      ctx.json({
        total_rows: 1500,
        page_size: 500,
        page_count: 3,
        current_page: parseInt(page),
        columns: ['id', 'name'],
        rows: [[1, 'Test']],
      })
    );
  }),

  // CSV export
  rest.get('/api/queries/:id/export', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.set('Content-Type', 'text/csv'),
      ctx.body('id,name\n1,Test\n')
    );
  }),
];
```

```typescript
// mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

```typescript
// vitest.setup.ts
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from './mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

---

## Accessibility Testing

### Automated Accessibility Audits

#### Using Lighthouse

1. Open Chrome DevTools (F12)
2. Navigate to **Lighthouse** tab
3. Select **Accessibility** category
4. Click **Analyze page load**

**Target Score**: ≥ 95/100

#### Using axe DevTools

```bash
# Install axe browser extension
# Chrome: https://chrome.google.com/webstore (search "axe DevTools")
# Firefox: https://addons.mozilla.org (search "axe DevTools")
```

1. Open axe DevTools panel
2. Click **Scan ALL of my page**
3. Review and fix all violations

### Manual Accessibility Checklist

#### Keyboard Navigation

- [ ] Tab through all interactive elements in logical order
- [ ] Visible focus indicators on all focusable elements
- [ ] Enter key submits form when textarea is focused
- [ ] Escape key closes modals/toasts (if applicable)
- [ ] No keyboard traps

#### Screen Reader Testing

**Tools**: NVDA (Windows), JAWS (Windows), VoiceOver (Mac)

**Steps**:
1. Enable screen reader
2. Navigate through interface
3. Verify announcements

**Checklist**:
- [ ] All form inputs have associated labels
- [ ] ARIA live regions announce dynamic content changes
- [ ] Loading states announced (aria-busy)
- [ ] Error messages announced immediately (aria-live="assertive")
- [ ] Buttons have descriptive aria-labels
- [ ] Tables have proper headers and captions
- [ ] Hidden decorative elements (aria-hidden="true")

#### Color Contrast

Use browser extension: **WAVE** or **Accessibility Insights**

**Requirements**:
- [ ] Normal text: ≥ 4.5:1 contrast ratio
- [ ] Large text (≥18pt): ≥ 3:1 contrast ratio
- [ ] UI components: ≥ 3:1 contrast ratio

#### Touch Target Sizes (Mobile)

- [ ] All interactive elements ≥ 44px × 44px on mobile
- [ ] Adequate spacing between touch targets (≥8px)

---

## Performance Testing

### Metrics to Measure

1. **Initial Load Time**
2. **Time to Interactive (TTI)**
3. **First Contentful Paint (FCP)**
4. **Largest Contentful Paint (LCP)**
5. **Bundle Size**

### Tools

#### Lighthouse Performance Audit

**Target Scores**:
- Performance: ≥ 90
- First Contentful Paint: < 1.8s
- Largest Contentful Paint: < 2.5s
- Time to Interactive: < 3.8s

#### Bundle Analysis

```bash
# Install bundle analyzer
npm install --save-dev vite-plugin-visualizer

# Add to vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: true })
  ]
});

# Build and analyze
npm run build
```

**Target Bundle Size**: < 500KB (gzipped)

### Performance Test Cases

#### Test Case: Large Result Set Rendering

**Steps**:
1. Execute query returning 500 rows × 20 columns
2. Measure rendering time
3. Test scrolling performance

**Expected Results**:
- ✅ Table renders in < 1 second
- ✅ Smooth scrolling (60fps)
- ✅ No UI freezing
- ✅ Pagination loads new page in < 500ms

#### Test Case: Rapid Interactions

**Steps**:
1. Rapidly click between pages (10 times)
2. Rapidly submit queries (if not rate-limited)
3. Monitor memory usage

**Expected Results**:
- ✅ No memory leaks
- ✅ No cumulative layout shift
- ✅ Responsive UI throughout

---

## Browser Compatibility

### Supported Browsers

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest 2 versions | ✅ Primary |
| Firefox | Latest 2 versions | ✅ Primary |
| Safari | Latest 2 versions | ✅ Primary |
| Edge | Latest 2 versions | ✅ Primary |
| Mobile Safari | iOS 14+ | ✅ Secondary |
| Chrome Mobile | Latest | ✅ Secondary |

### Features to Test in Each Browser

- [ ] CSS Grid layout
- [ ] CSS Flexbox
- [ ] Fetch API
- [ ] Clipboard API
- [ ] SessionStorage
- [ ] Syntax highlighting display
- [ ] File download (CSV export)
- [ ] CSS animations
- [ ] Smooth scrolling

### Known Browser Differences

**Safari**:
- Clipboard API requires user interaction (works correctly)
- Date input styling differs (acceptable)

**Firefox**:
- Scrollbar styling not supported (acceptable fallback)

**Edge**:
- Should behave identically to Chrome (Chromium-based)

---

## Bug Reporting Template

When reporting bugs, use the following template:

```markdown
## Bug Report

**Summary**: [Brief description]

**Severity**: [Critical / High / Medium / Low]

**Component**: [QueryForm / SqlPreview / ResultsTable / etc.]

**Steps to Reproduce**:
1. [First step]
2. [Second step]
3. [Third step]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Screenshots/Videos**:
[Attach if applicable]

**Environment**:
- Browser: [Chrome 120 / Firefox 121 / etc.]
- OS: [Windows 11 / macOS 14 / Ubuntu 22.04]
- Screen Size: [1920×1080 / 375×667 mobile]
- Backend API Version: [v1.0.0]

**Console Errors**:
```
[Paste any console errors here]
```

**Network Tab**:
- Request URL: [e.g., POST /api/queries]
- Status Code: [e.g., 500]
- Response: [Paste response if relevant]

**Additional Context**:
[Any other relevant information]
```

---

## Test Execution Tracking

### Test Run Template

```markdown
## Test Run: [Date]

**Tester**: [Name]
**Build**: [Commit hash or version]
**Environment**: [Development / Staging / Production]

### Results Summary

| Category | Total Tests | Passed | Failed | Skipped |
|----------|-------------|--------|--------|---------|
| Query Submission | 6 | 6 | 0 | 0 |
| SQL Preview | 5 | 5 | 0 | 0 |
| Results Display | 4 | 4 | 0 | 0 |
| Pagination | 6 | 5 | 1 | 0 |
| Error Handling | 6 | 6 | 0 | 0 |
| UX Features | 4 | 4 | 0 | 0 |
| Responsive | 3 | 3 | 0 | 0 |
| **TOTAL** | **34** | **33** | **1** | **0** |

### Failed Tests

1. **Test Case 4.3: Navigate to Previous Page**
   - **Reason**: Auto-scroll not working on page change
   - **Bug ID**: #123
   - **Assigned To**: [Developer]

### Notes

[Any additional observations or comments]
```

---

## Continuous Integration (CI) Setup

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Frontend Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci
      working-directory: ./frontend

    - name: Run linter
      run: npm run lint
      working-directory: ./frontend

    - name: Run type check
      run: npm run type-check
      working-directory: ./frontend

    - name: Run unit tests
      run: npm run test:unit
      working-directory: ./frontend

    - name: Run integration tests
      run: npm run test:integration
      working-directory: ./frontend

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./frontend/coverage/coverage-final.json
```

---

## Summary

This testing guide covers:

✅ **Manual Testing**: 40+ detailed test cases
✅ **Automated Testing**: Unit and integration test examples
✅ **Accessibility**: WCAG 2.1 AA compliance checklist
✅ **Performance**: Metrics and optimization targets
✅ **Browser Compatibility**: Cross-browser testing matrix
✅ **Bug Reporting**: Standardized template

### Next Steps

1. **Execute Manual Tests**: Run through all test cases in this guide
2. **Set Up Automated Tests**: Implement unit and integration tests
3. **CI/CD Integration**: Add automated testing to deployment pipeline
4. **Performance Monitoring**: Set up ongoing performance tracking
5. **Accessibility Audit**: Schedule regular accessibility reviews

**Testing Priority**: 🔥 High - All user-facing features should be tested before deployment

---

**Document Version**: 1.0
**Last Updated**: 2025-11-05
**Author**: SQL AI Agent Team
**Status**: ✅ Ready for Use
