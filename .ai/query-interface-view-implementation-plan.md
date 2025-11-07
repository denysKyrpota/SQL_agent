# View Implementation Plan: Query Interface View

## 1. Overview

The Query Interface View is the primary workspace of the SQL AI Agent application where users submit natural language questions and execute SQL queries. This view handles the complete query workflow from input through SQL generation, preview, execution, and results display. It serves as the main landing page for authenticated users and supports the core value proposition of translating natural language to SQL with transparent preview and execution.

**View Purpose**: Enable users to ask database questions in natural language, review generated SQL, execute queries, and view/export results without SQL knowledge.

**Primary User Stories**: US-003, US-004, US-005, US-006, US-007, US-008, US-009, US-010, US-011, US-015, US-016, US-021, US-022, US-023

## 2. View Routing

**Path**: `/` or `/query`

**Route Protection**: Protected route requiring authentication

**Access Level**: All authenticated users (both 'user' and 'admin' roles)

**Layout**: MainLayout (persistent header with navigation and user menu)

## 3. Component Structure

```
QueryInterfaceView
├── QueryForm
│   ├── TextArea (natural language input)
│   ├── CharacterCount
│   ├── ExampleQuestions
│   └── Button (Generate SQL)
│
├── LoadingIndicator (conditional)
│   └── LoadingStage (schema/generation/execution)
│
├── SqlPreviewSection (conditional)
│   ├── SqlPreview
│   │   ├── SyntaxHighlighter
│   │   └── LineNumbers
│   ├── Button (Copy SQL)
│   └── Button (Execute Query)
│
├── ErrorAlert (conditional)
│   ├── ErrorIcon
│   ├── ErrorMessage
│   └── Button (Try Again)
│
└── ResultsSection (conditional)
    ├── PerformanceMetrics
    │   ├── GenerationTime
    │   └── ExecutionTime
    ├── ResultsTable
    │   ├── TableHeader
    │   └── TableBody
    ├── Pagination
    │   ├── Button (Previous)
    │   ├── PageInfo
    │   └── Button (Next)
    └── Button (Export CSV)
```

## 4. Component Details

### QueryInterfaceView (Main Container)

**Component Description**: Root container component that orchestrates the entire query workflow, managing state transitions between input, generation, execution, and results display.

**Main HTML Elements**:
- `<main>` - Semantic main content wrapper with ARIA label
- `<div className="query-interface-container">` - Centered content area with max-width 1200px
- `<section>` elements for each workflow stage

**Handled Events**:
- Query submission (via QueryForm)
- SQL execution trigger
- Result pagination
- CSV export
- Retry after error
- Window beforeunload (warn about unsaved work)

**Validation Conditions**:
- Natural language query: 1-5000 characters, not only whitespace
- Query must have generated SQL before execution can be triggered
- Results must exist before pagination or export
- User must be authenticated (checked by route guard)

**Types**:
- `QueryInterfaceState` (ViewModel)
- `CreateQueryRequest` (API DTO)
- `QueryAttemptResponse` (API DTO)
- `ExecuteQueryResponse` (API DTO)
- `QueryResultsResponse` (API DTO)

**Props**: None (top-level view component)

---

### QueryForm

**Component Description**: Form component for natural language query input, providing textarea, character count, example questions, and submission button.

**Main HTML Elements**:
- `<form onSubmit={handleSubmit}>` - Form wrapper with submit handler
- `<label htmlFor="query-input">` - Accessible label for textarea
- `<div className="form-controls">` - Container for input and metadata
- `<div className="form-actions">` - Container for submit button

**Child Components**:
- `TextArea` - Multi-line input for natural language query
- `CharacterCount` - Live character counter with limit display
- `ExampleQuestions` - Clickable example queries
- `Button` - Submit button labeled "Generate SQL"

**Handled Events**:
- `onSubmit` - Form submission to generate SQL
- `onChange` - Text input changes to update character count and enable/disable submit
- `onExampleSelect` - Click on example question to populate textarea

**Validation Conditions**:
- Input must not be empty (after trim)
- Input must be 1-5000 characters
- Input must not be only whitespace
- Submit button disabled during generation or execution
- Submit button disabled when input is invalid

**Types**:
- `QueryFormProps` - `{ value: string; onChange: (value: string) => void; onSubmit: () => void; disabled: boolean; examples: string[] }`
- `string` for input value
- `boolean` for validation states

**Props**:
```typescript
interface QueryFormProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  examples: string[];
}
```

---

### TextArea

**Component Description**: Multi-line text input component with auto-resize, character limit enforcement, and accessibility features.

**Main HTML Elements**:
- `<div className="textarea-wrapper">` - Container for textarea and metadata
- `<textarea>` - Input element with auto-resize
- `<label>` - Associated label with htmlFor attribute

**Handled Events**:
- `onChange` - Text input changes, triggers parent update
- `onFocus` - Focus state for styling
- `onBlur` - Blur state for validation display
- `onKeyDown` - Capture special keys (e.g., Ctrl+Enter for submit)

**Validation Conditions**:
- Maximum 5000 characters (hard limit via maxLength)
- Warning visual state at 90% capacity (4500 chars)
- Error state if attempting to exceed limit
- Required field validation (cannot be empty on submit)

**Types**:
- `TextAreaProps` - component interface
- `string` for value
- `number` for maxLength
- `boolean` for disabled state

**Props**:
```typescript
interface TextAreaProps {
  value: string;
  onChange: (value: string) => void;
  maxLength: number;
  placeholder: string;
  disabled: boolean;
  autoFocus?: boolean;
  label: string;
  id: string;
}
```

---

### CharacterCount

**Component Description**: Display component showing current character count with visual feedback as limit approaches.

**Main HTML Elements**:
- `<div className="character-count">` - Container with dynamic styling based on count
- `<span className="current">{currentCount}</span>` - Current character count
- `<span className="separator">/</span>` - Visual separator
- `<span className="max">{maxCount}</span>` - Maximum character limit

**Handled Events**: None (display only)

**Validation Conditions**:
- Color changes at thresholds:
  - 0-4000 chars: neutral color
  - 4001-4500 chars: warning color (yellow)
  - 4501-4900 chars: danger color (orange)
  - 4901-5000 chars: critical color (red)
- ARIA live region announces at key thresholds

**Types**:
- `CharacterCountProps` - `{ current: number; max: number }`
- `number` for counts

**Props**:
```typescript
interface CharacterCountProps {
  current: number;
  max: number;
}
```

---

### ExampleQuestions

**Component Description**: Display component showing clickable example questions to help users understand query patterns.

**Main HTML Elements**:
- `<div className="example-questions">` - Container
- `<h3>` - Section heading "Example Questions"
- `<ul className="examples-list">` - Semantic list
- `<li>` - Individual example items
- `<button type="button">` - Clickable example buttons

**Handled Events**:
- `onClick` - Click on example to populate textarea

**Validation Conditions**:
- Examples should be disabled when form is disabled (during generation/execution)
- Click should replace current textarea content (not append)

**Types**:
- `ExampleQuestionsProps` - `{ examples: string[]; onSelect: (example: string) => void; disabled: boolean }`
- `string[]` for examples array

**Props**:
```typescript
interface ExampleQuestionsProps {
  examples: string[];
  onSelect: (example: string) => void;
  disabled: boolean;
}
```

---

### LoadingIndicator

**Component Description**: Two-stage loading indicator showing current processing stage with animated spinner and descriptive text.

**Main HTML Elements**:
- `<div className="loading-indicator">` - Container with centering
- `<div className="spinner">` - Animated CSS spinner or SVG
- `<p className="loading-text">` - Stage-specific message
- `<div aria-live="polite">` - Screen reader announcement region

**Handled Events**: None (display only)

**Validation Conditions**:
- Must display appropriate message based on stage:
  - 'schema': "Analyzing database schema..."
  - 'generation': "Generating SQL query..."
  - 'execution': "Running query..."
- Should show elapsed time after 10 seconds

**Types**:
- `LoadingIndicatorProps` - `{ stage: 'schema' | 'generation' | 'execution'; startTime?: Date }`
- `LoadingStage` type enum

**Props**:
```typescript
interface LoadingIndicatorProps {
  stage: 'schema' | 'generation' | 'execution';
  startTime?: Date;
}
```

---

### SqlPreviewSection

**Component Description**: Container component displaying generated SQL with syntax highlighting, copy functionality, and execution button.

**Main HTML Elements**:
- `<section className="sql-preview-section">` - Semantic section
- `<h2>` - Section heading "Generated SQL"
- `<div className="sql-preview-container">` - Preview wrapper
- `<div className="sql-actions">` - Action buttons container

**Child Components**:
- `SqlPreview` - Syntax-highlighted SQL display
- `Button` (Copy SQL)
- `Button` (Execute Query)

**Handled Events**:
- Copy SQL to clipboard
- Execute query
- Scroll into view when generated

**Validation Conditions**:
- Only displayed when `generated_sql` is not null
- Execute button disabled when execution is in progress
- Copy button shows confirmation feedback on click

**Types**:
- `SqlPreviewSectionProps` - component interface
- `string` for SQL content
- `boolean` for execution state

**Props**:
```typescript
interface SqlPreviewSectionProps {
  sql: string;
  onExecute: () => void;
  onCopy: () => void;
  executing: boolean;
}
```

---

### SqlPreview

**Component Description**: Display component showing SQL code with syntax highlighting and line numbers using react-syntax-highlighter or similar library.

**Main HTML Elements**:
- `<div className="sql-preview">` - Container
- `<pre className="line-numbers">` - Line numbers gutter
- `<code className="sql-code">` - Highlighted SQL code

**Handled Events**: None (display only, copy handled by parent)

**Validation Conditions**:
- SQL must be properly formatted with indentation
- Line numbers must match code lines
- Horizontal scroll for long lines
- Responsive: maintain readability on mobile

**Types**:
- `SqlPreviewProps` - `{ sql: string; showLineNumbers: boolean }`
- `string` for SQL content

**Props**:
```typescript
interface SqlPreviewProps {
  sql: string;
  showLineNumbers?: boolean;
  language?: string; // default: 'sql'
}
```

---

### ErrorAlert

**Component Description**: Contextual error message display with icon, message text, and optional action button for error recovery.

**Main HTML Elements**:
- `<div role="alert" className="error-alert">` - Alert container with ARIA role
- `<div className="error-icon">` - Icon container (error/warning icon)
- `<div className="error-content">` - Message and details
- `<p className="error-message">` - Primary error message
- `<p className="error-detail">` - Additional details (optional)
- `<div className="error-actions">` - Action buttons

**Handled Events**:
- `onDismiss` - Close/dismiss alert
- `onAction` - Primary action (e.g., "Try Again")

**Validation Conditions**:
- Display appropriate message based on error type:
  - `failed_generation`: "Unable to generate query. Try rephrasing your question."
  - `failed_execution`: "Query failed to execute. The generated SQL may be invalid."
  - `timeout`: "Query took too long to execute. Try narrowing your search."
- Include database error message for execution failures (if available)
- Dismissible with X button
- Auto-focus on action button for keyboard users

**Types**:
- `ErrorAlertProps` - component interface
- `ErrorType` - `'generation' | 'execution' | 'timeout' | 'validation' | 'network'`
- `string | null` for error message

**Props**:
```typescript
interface ErrorAlertProps {
  type: ErrorType;
  message: string;
  detail?: string | null;
  dismissible?: boolean;
  onDismiss?: () => void;
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

---

### ResultsSection

**Component Description**: Container component displaying query execution results including performance metrics, data table, pagination, and export functionality.

**Main HTML Elements**:
- `<section className="results-section">` - Semantic section
- `<h2>` - Section heading "Query Results"
- `<div className="results-header">` - Metrics and actions
- `<div className="results-content">` - Table container

**Child Components**:
- `PerformanceMetrics` - Execution timing display
- `ResultsTable` - Data grid
- `Pagination` - Page navigation
- `Button` (Export CSV)

**Handled Events**:
- Page navigation
- CSV export
- Scroll into view when results appear

**Validation Conditions**:
- Only displayed when query status is 'success'
- Pagination only shown if total_rows > page_size (500)
- Export button warns if results exceed 10,000 rows
- Empty state message if total_rows === 0

**Types**:
- `ResultsSectionProps` - component interface
- `QueryResults` - results data structure
- `number` for current page

**Props**:
```typescript
interface ResultsSectionProps {
  results: QueryResults;
  currentPage: number;
  onPageChange: (page: number) => void;
  onExport: () => void;
  generationTimeMs: number;
  executionTimeMs: number;
}
```

---

### PerformanceMetrics

**Component Description**: Display component showing query performance information including SQL generation time and execution time.

**Main HTML Elements**:
- `<div className="performance-metrics">` - Container
- `<div className="metric">` - Individual metric item
- `<span className="metric-label">` - Metric label
- `<span className="metric-value">` - Metric value with unit

**Handled Events**: None (display only)

**Validation Conditions**:
- Format times appropriately:
  - < 1000ms: show in milliseconds
  - >= 1000ms: show in seconds with 1 decimal place
- Color coding based on performance:
  - Green: < 5 seconds
  - Yellow: 5-30 seconds
  - Red: > 30 seconds
- Only show generation time if available
- Only show execution time if query was executed

**Types**:
- `PerformanceMetricsProps` - `{ generationTimeMs: number | null; executionTimeMs: number | null; rowCount: number | null }`
- `number | null` for timing values

**Props**:
```typescript
interface PerformanceMetricsProps {
  generationTimeMs: number | null;
  executionTimeMs: number | null;
  rowCount: number | null;
}
```

---

### ResultsTable

**Component Description**: Data grid component displaying query results with proper table semantics, responsive columns, and alternating row colors.

**Main HTML Elements**:
- `<div className="results-table-wrapper">` - Container with horizontal scroll
- `<table className="results-table">` - Semantic table element
- `<thead>` - Table header
- `<tr>` - Header row
- `<th scope="col">` - Column headers
- `<tbody>` - Table body
- `<tr>` - Data rows
- `<td>` - Data cells

**Handled Events**:
- Horizontal scroll (for responsive mobile view)
- Copy cell value on click (optional enhancement)

**Validation Conditions**:
- Column widths based on data type detection:
  - Narrow (100px): IDs, small numbers, booleans
  - Medium (150px): Dates, medium text
  - Wide (200-300px): Long text, descriptions
- Cell content truncation with title attribute for full text on hover
- Alternating row colors for readability
- Frozen first column on mobile
- Empty state if no rows returned
- Proper handling of null values (display as "NULL" or "-")

**Types**:
- `ResultsTableProps` - component interface
- `string[]` for columns
- `Array<Array<any>>` for rows
- `ColumnType` - `'id' | 'number' | 'date' | 'text' | 'boolean'`

**Props**:
```typescript
interface ResultsTableProps {
  columns: string[];
  rows: Array<Array<any>>;
  totalRows: number;
}
```

---

### Pagination

**Component Description**: Page navigation component for large result sets with Previous/Next buttons and page information display.

**Main HTML Elements**:
- `<nav aria-label="Results pagination" className="pagination">` - Semantic navigation
- `<button type="button" aria-label="Previous page">` - Previous button
- `<div className="pagination-info">` - Page info display
- `<span className="page-indicator">` - "Page X of Y"
- `<button type="button" aria-label="Next page">` - Next button

**Handled Events**:
- `onPrevious` - Navigate to previous page
- `onNext` - Navigate to next page
- Keyboard navigation (Arrow keys)

**Validation Conditions**:
- Previous button disabled on page 1
- Next button disabled on last page
- Page numbers must be valid (1 to total_pages)
- Announce page changes to screen readers
- Display format: "Page 2 of 5" or "Showing 501-1000 of 1500 rows"

**Types**:
- `PaginationProps` - component interface
- `number` for page numbers

**Props**:
```typescript
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalRows: number;
  onPageChange: (page: number) => void;
}
```

---

### Button (Reusable)

**Component Description**: Reusable action button component with variants, loading states, and icon support.

**Main HTML Elements**:
- `<button type="button" className="btn">` - Button element with dynamic classes

**Handled Events**:
- `onClick` - Click handler
- Keyboard events (Enter, Space)

**Validation Conditions**:
- Disabled state prevents clicks
- Loading state shows spinner and disables interaction
- Proper focus indicators
- Accessible labels
- Support for icons (left-aligned)

**Types**:
- `ButtonProps` - component interface
- `ButtonVariant` - `'primary' | 'secondary' | 'danger'`
- `ReactNode` for children and icon

**Props**:
```typescript
interface ButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit';
  icon?: React.ReactNode;
  fullWidth?: boolean;
  ariaLabel?: string;
}
```

## 5. Types

### Core ViewModel Types

```typescript
/**
 * Main state interface for Query Interface View
 */
interface QueryInterfaceState {
  // Input state
  naturalLanguageQuery: string;

  // Query attempt state
  queryId: number | null;
  generatedSql: string | null;
  status: QueryStatus;

  // Timing
  generationTimeMs: number | null;
  executionTimeMs: number | null;

  // Results state
  results: QueryResults | null;
  currentPage: number;

  // Error state
  error: QueryError | null;

  // UI state
  isGenerating: boolean;
  isExecuting: boolean;
  loadingStage: LoadingStage | null;
}

/**
 * Loading stage enum for multi-stage generation
 */
type LoadingStage = 'schema' | 'generation' | 'execution';

/**
 * Query error structure
 */
interface QueryError {
  type: ErrorType;
  message: string;
  detail?: string | null;
}

/**
 * Error type enum
 */
type ErrorType =
  | 'validation'
  | 'generation'
  | 'execution'
  | 'timeout'
  | 'network';

/**
 * Example questions configuration
 */
interface ExampleQuestion {
  text: string;
  category?: string;
}
```

### API DTO Types (from existing types)

Used from `frontend/src/types/api.ts`:
- `CreateQueryRequest` - Request for POST /queries
- `QueryAttemptResponse` - Response from POST /queries
- `ExecuteQueryResponse` - Response from POST /queries/{id}/execute
- `QueryResultsResponse` - Response from GET /queries/{id}/results

Used from `frontend/src/types/models.ts`:
- `QueryResults` - Results data structure
- `QueryStatus` - Status enum

Used from `frontend/src/types/common.ts`:
- `ISO8601Timestamp` - Timestamp type

### Component Props Types

All component prop interfaces defined in section 4 (Component Details).

## 6. State Management

### State Location

**Local Component State** (React useState hooks in QueryInterfaceView):
- All state for this view is managed locally within the QueryInterfaceView component
- No global state management (Context, Redux) required for MVP
- State persists across component lifecycle but resets on unmount

### State Structure

```typescript
const [queryState, setQueryState] = useState<QueryInterfaceState>({
  naturalLanguageQuery: '',
  queryId: null,
  generatedSql: null,
  status: 'not_executed',
  generationTimeMs: null,
  executionTimeMs: null,
  results: null,
  currentPage: 1,
  error: null,
  isGenerating: false,
  isExecuting: false,
  loadingStage: null,
});
```

### State Persistence

**SessionStorage** for input preservation:
```typescript
// Save input on change
const handleInputChange = (value: string) => {
  setQueryState(prev => ({ ...prev, naturalLanguageQuery: value }));
  sessionStorage.setItem('queryInputText', value);
};

// Restore on mount
useEffect(() => {
  const savedInput = sessionStorage.getItem('queryInputText');
  if (savedInput) {
    setQueryState(prev => ({ ...prev, naturalLanguageQuery: savedInput }));
  }
}, []);

// Clear on successful execution
const clearStoredInput = () => {
  sessionStorage.removeItem('queryInputText');
};
```

### State Transitions

```
Initial State:
  status: 'not_executed'
  isGenerating: false
  isExecuting: false
  error: null

User submits query →
  isGenerating: true
  loadingStage: 'schema'
  error: null

Schema analysis complete →
  loadingStage: 'generation'

SQL generated successfully →
  isGenerating: false
  loadingStage: null
  generatedSql: <sql>
  queryId: <id>
  status: 'not_executed'
  generationTimeMs: <time>

SQL generation failed →
  isGenerating: false
  loadingStage: null
  status: 'failed_generation'
  error: { type: 'generation', message: '...' }

User clicks execute →
  isExecuting: true
  loadingStage: 'execution'

Execution completes successfully →
  isExecuting: false
  loadingStage: null
  status: 'success'
  executionTimeMs: <time>
  results: <data>

Execution fails →
  isExecuting: false
  loadingStage: null
  status: 'failed_execution'
  error: { type: 'execution', message: '...', detail: '...' }

User clicks "Try Again" →
  Reset to initial state (clear error, generated SQL, results)
  Preserve naturalLanguageQuery for editing
```

### Custom Hook (Optional Extraction)

For code organization, state management logic can be extracted into a custom hook:

```typescript
/**
 * Custom hook for query interface state management
 */
function useQueryInterface() {
  const [queryState, setQueryState] = useState<QueryInterfaceState>({...});

  const submitQuery = async (naturalLanguageQuery: string) => { ... };
  const executeQuery = async () => { ... };
  const loadResults = async (page: number) => { ... };
  const exportCSV = async () => { ... };
  const resetQuery = () => { ... };

  return {
    queryState,
    actions: {
      submitQuery,
      executeQuery,
      loadResults,
      exportCSV,
      resetQuery,
    },
  };
}
```

## 7. API Integration

### API Endpoints Used

1. **POST /queries** - Submit natural language query and generate SQL
2. **POST /queries/{id}/execute** - Execute generated SQL
3. **GET /queries/{id}/results** - Fetch paginated results
4. **GET /queries/{id}/export** - Download CSV export

### Request/Response Flow

#### Query Submission

**Request**:
```typescript
const submitQuery = async (naturalLanguageQuery: string) => {
  const request: CreateQueryRequest = {
    natural_language_query: naturalLanguageQuery.trim()
  };

  const response = await fetch('/api/queries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    credentials: 'include', // Include session cookie
  });

  if (!response.ok) {
    throw new APIError(response.status, await response.json());
  }

  return await response.json() as QueryAttemptResponse;
};
```

**Response Type**: `QueryAttemptResponse`
```typescript
{
  id: number;
  natural_language_query: string;
  generated_sql: string | null;
  status: QueryStatus; // 'not_executed' or 'failed_generation'
  created_at: ISO8601Timestamp;
  generated_at: ISO8601Timestamp | null;
  generation_ms: number | null;
  error_message: string | null;
}
```

**Error Handling**:
- 400: Validation error (empty query, too long)
- 401: Session expired (redirect to login)
- 429: Rate limit exceeded (show retry message)
- 503: LLM service unavailable (show service error)

#### Query Execution

**Request**:
```typescript
const executeQuery = async (queryId: number) => {
  const response = await fetch(`/api/queries/${queryId}/execute`, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new APIError(response.status, await response.json());
  }

  return await response.json() as ExecuteQueryResponse;
};
```

**Response Type**: `ExecuteQueryResponse`
```typescript
{
  id: number;
  status: QueryStatus; // 'success', 'failed_execution', or 'timeout'
  executed_at: ISO8601Timestamp;
  execution_ms: number;
  results: QueryResults | null;
  error_message: string | null;
}
```

**Error Handling**:
- 400: Query not in executable state
- 401: Session expired
- 403: User doesn't own this query
- 404: Query not found

#### Results Pagination

**Request**:
```typescript
const loadResults = async (queryId: number, page: number) => {
  const response = await fetch(
    `/api/queries/${queryId}/results?page=${page}`,
    { credentials: 'include' }
  );

  if (!response.ok) {
    throw new APIError(response.status, await response.json());
  }

  return await response.json() as QueryResultsResponse;
};
```

**Response Type**: `QueryResultsResponse`
```typescript
{
  attempt_id: number;
  total_rows: number;
  page_size: number;
  page_count: number;
  current_page: number;
  columns: string[];
  rows: Array<Array<any>>;
}
```

#### CSV Export

**Request**:
```typescript
const exportCSV = async (queryId: number) => {
  const response = await fetch(
    `/api/queries/${queryId}/export`,
    { credentials: 'include' }
  );

  if (!response.ok) {
    throw new APIError(response.status, await response.json());
  }

  // Trigger download
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `query_${queryId}_${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};
```

**Response**: CSV file download (Content-Type: text/csv)

**Error Handling**:
- 404: Query not found or not executed
- 413: Results exceed 10,000 row limit (show warning)

### Authentication Handling

All API calls include session cookie via `credentials: 'include'`. 401 responses trigger redirect to login:

```typescript
// Axios interceptor or fetch wrapper
if (response.status === 401) {
  // Clear auth context
  authContext.logout();
  // Redirect to login with return URL
  navigate('/login', { state: { from: location.pathname } });
}
```

## 8. User Interactions

### Query Submission Flow

1. **User types question** in textarea
   - Character count updates live
   - Submit button enables when valid (1-5000 chars, not empty)
   - Input saved to sessionStorage on change

2. **User clicks example question**
   - Textarea populated with example text
   - Character count updates
   - Submit button enables

3. **User clicks "Generate SQL"**
   - Form submits
   - Loading indicator appears with stage "Analyzing database schema..."
   - Submit button disabled
   - API call: POST /queries

4. **SQL generation completes**
   - Loading stage changes to "Generating SQL query..."
   - Wait for API response

5. **SQL preview appears**
   - Loading indicator disappears
   - Generated SQL displays with syntax highlighting
   - Copy and Execute buttons appear
   - Auto-scroll to SQL preview section
   - Generation time displayed

6. **User reviews SQL**
   - User can read highlighted SQL
   - User can copy SQL to clipboard (shows "Copied!" toast)
   - User decides whether to execute

7. **User clicks "Execute Query"**
   - Loading indicator appears with stage "Running query..."
   - Execute button disabled
   - API call: POST /queries/{id}/execute

8. **Results appear**
   - Loading indicator disappears
   - Results table displays
   - Performance metrics show generation + execution time
   - Pagination appears if > 500 rows
   - Export CSV button appears
   - Auto-scroll to results section

### Error Recovery Flow

1. **Generation fails**
   - Error alert appears: "Unable to generate query. Try rephrasing your question."
   - "Try Again" button available
   - User can edit question and resubmit
   - Clicking "Try Again" clears error and resets form

2. **Execution fails**
   - Error alert appears: "Query failed to execute. The generated SQL may be invalid."
   - Database error message shown (if available)
   - "Try Again" button available
   - User can return to editing question
   - Generated SQL remains visible for reference

3. **Timeout occurs**
   - Error alert appears: "Query took too long to execute. Try narrowing your search."
   - Suggestion to make query more specific
   - "Try Again" button available

### Pagination Interaction

1. **User clicks "Next"**
   - API call: GET /queries/{id}/results?page={currentPage + 1}
   - Loading state on table
   - Table updates with new rows
   - Previous button becomes enabled
   - Next button disabled if last page

2. **User clicks "Previous"**
   - API call: GET /queries/{id}/results?page={currentPage - 1}
   - Table updates with previous page rows
   - Next button becomes enabled
   - Previous button disabled if first page

### CSV Export Interaction

1. **User clicks "Export CSV"**
   - API call: GET /queries/{id}/export
   - Export button shows loading state
   - Browser downloads CSV file
   - Toast notification: "CSV exported successfully"
   - If results > 10,000 rows, warning toast: "Export limited to 10,000 rows"

### Keyboard Interactions

- **Tab**: Navigate through form fields and buttons
- **Enter** in textarea: Submit form (Ctrl+Enter on Windows, Cmd+Enter on Mac)
- **Escape**: Clear error alert if dismissible
- **Arrow keys** in pagination: Navigate pages (optional enhancement)

## 9. Conditions and Validation

### Input Validation

**Natural Language Query Field**:

1. **Required Field**
   - Condition: Field cannot be empty (after trim)
   - Validation: Check on submit
   - Error Message: "Please enter a question"
   - UI Indication: Submit button disabled

2. **Minimum Length**
   - Condition: At least 1 character after trim
   - Validation: Check on submit
   - Error Message: "Question is too short"
   - UI Indication: Submit button disabled

3. **Maximum Length**
   - Condition: No more than 5000 characters
   - Validation: Check on input (hard limit via maxLength)
   - Error Message: "Question exceeds 5000 character limit"
   - UI Indication: Character count turns red, input blocked

4. **Whitespace Only**
   - Condition: Cannot be only whitespace characters
   - Validation: Check on submit
   - Error Message: "Please enter a valid question"
   - UI Indication: Submit button disabled

**Validation Implementation**:
```typescript
const validateQuery = (query: string): string | null => {
  const trimmed = query.trim();

  if (trimmed.length === 0) {
    return "Please enter a question";
  }

  if (trimmed.length > 5000) {
    return "Question exceeds 5000 character limit";
  }

  if (query.length > 0 && trimmed.length === 0) {
    return "Please enter a valid question";
  }

  return null; // Valid
};
```

### Execution Conditions

**Execute Button Enabled When**:
1. Generated SQL is not null
2. Status is 'not_executed'
3. Not currently executing
4. User owns the query (enforced by API)

**Execute Button Disabled When**:
1. No SQL has been generated
2. Currently generating SQL
3. Currently executing query
4. Query already executed (status is 'success', 'failed_execution', or 'timeout')

### Pagination Conditions

**Pagination Displayed When**:
- Query status is 'success'
- Total rows > page_size (500)

**Previous Button**:
- Enabled: currentPage > 1
- Disabled: currentPage === 1

**Next Button**:
- Enabled: currentPage < totalPages
- Disabled: currentPage === totalPages

### Export Conditions

**Export Button Displayed When**:
- Query status is 'success'
- Results exist

**Export Warning When**:
- Total rows > 10,000
- Message: "Export limited to first 10,000 rows"

### API Condition Validation

**Backend validates** (frontend should not bypass):

1. **Authentication**
   - User must have valid session
   - Session not expired
   - Session not revoked

2. **Authorization**
   - User must own the query (or be admin)
   - Enforced on execute, results, export endpoints

3. **Query State**
   - SQL must be generated before execution
   - Query must be executed before viewing results
   - Query must be successful before export

4. **Rate Limiting**
   - Max 10 query submissions per minute per user
   - Max 5 executions per minute per user

## 10. Error Handling

### Error Categories

#### 1. Validation Errors (Client-Side)

**Empty Query Submission**:
- **Detection**: Before API call, check trimmed length
- **Handling**: Show inline error below textarea
- **Message**: "Please enter a question"
- **Recovery**: User edits input and resubmits

**Character Limit Exceeded**:
- **Detection**: On input, check length
- **Handling**: Block further input, show error state
- **Message**: "Question exceeds 5000 character limit"
- **Recovery**: User deletes characters to get under limit

#### 2. Generation Errors (API)

**LLM Service Unavailable**:
- **Detection**: 503 response from POST /queries
- **Handling**: Show error alert
- **Message**: "Service temporarily unavailable. Please try again."
- **Recovery**: "Try Again" button to retry submission
- **Implementation**: Automatic 3 retries on backend, frontend shows final failure

**Generation Failed**:
- **Detection**: Response status 'failed_generation'
- **Handling**: Show error alert
- **Message**: "Unable to generate query. Try rephrasing your question."
- **Recovery**: "Try Again" button clears form, user can edit and resubmit

**Rate Limit Exceeded**:
- **Detection**: 429 response from POST /queries
- **Handling**: Show error alert
- **Message**: "Too many requests. Please wait a moment and try again."
- **Recovery**: "Try Again" button (user must wait before retrying)

#### 3. Execution Errors (API)

**SQL Execution Failed**:
- **Detection**: Response status 'failed_execution'
- **Handling**: Show error alert with database error details
- **Message**: "Query failed to execute. The generated SQL may be invalid."
- **Detail**: Include database error message (e.g., "Column 'customer_address' does not exist")
- **Recovery**: "Try Again" button, user can rephrase question

**Query Timeout**:
- **Detection**: Response status 'timeout'
- **Handling**: Show error alert
- **Message**: "Query took too long to execute. Try narrowing your search."
- **Recovery**: "Try Again" button with suggestion to be more specific

**Invalid Query State**:
- **Detection**: 400 response from POST /queries/{id}/execute
- **Handling**: Show error alert
- **Message**: "Cannot execute query in current state."
- **Recovery**: Reload page or return to query submission

#### 4. Authentication Errors

**Session Expired**:
- **Detection**: 401 response from any API call
- **Handling**: Clear auth context, redirect to login
- **Message**: "Your session has expired. Please log in again." (on login page)
- **Recovery**: User logs in, returns to query interface
- **Data Preservation**: Query input saved in sessionStorage, restored after login

**Insufficient Permissions**:
- **Detection**: 403 response from API call
- **Handling**: Show error alert or redirect
- **Message**: "You don't have permission to access this resource."
- **Recovery**: Contact admin or return to main interface

#### 5. Network Errors

**No Internet Connection**:
- **Detection**: Fetch API throws network error
- **Handling**: Show error alert
- **Message**: "Network error. Please check your internet connection."
- **Recovery**: "Try Again" button to retry request

**Request Timeout**:
- **Detection**: AbortController timeout
- **Handling**: Show error alert
- **Message**: "Request timed out. Please try again."
- **Recovery**: "Try Again" button

#### 6. System Errors

**Unexpected API Error**:
- **Detection**: 500 response or unhandled error
- **Handling**: Show generic error alert
- **Message**: "An unexpected error occurred. Please try again."
- **Recovery**: "Try Again" button, log error details to console

**React Component Error**:
- **Detection**: ErrorBoundary catches render error
- **Handling**: Show fallback UI
- **Message**: "Something went wrong. Please refresh the page."
- **Recovery**: "Refresh Page" button

### Error Display Strategy

**Inline Errors** (field-level):
- Used for: Form validation errors
- Location: Below input field
- Style: Red text with error icon
- Dismissal: Auto-dismiss when input changes

**Alert Errors** (view-level):
- Used for: API errors, generation/execution failures
- Location: Above content, below header
- Style: Red/orange box with icon and message
- Dismissal: Dismissible with X button or action button
- Persistence: Remains until dismissed or next action

**Toast Notifications** (system-level):
- Used for: Network errors, session expiration warnings
- Location: Top-right corner
- Style: Slide-in notification
- Dismissal: Auto-dismiss after 5 seconds or manual dismiss

### Error Logging

**Console Logging** (Development):
```typescript
console.error('Query submission failed:', {
  error,
  queryText: naturalLanguageQuery,
  timestamp: new Date().toISOString(),
});
```

**Error Reporting** (Production - Future):
- Send to error tracking service (Sentry, LogRocket)
- Include: error message, stack trace, user ID, timestamp
- Exclude: sensitive query content

## 11. Implementation Steps

### Step 1: Project Setup and Component Structure
1. Create component directory structure:
   ```
   frontend/src/views/QueryInterfaceView/
   ├── index.tsx (main view)
   ├── QueryInterfaceView.module.css
   ├── components/
   │   ├── QueryForm/
   │   ├── SqlPreviewSection/
   │   ├── ResultsSection/
   │   ├── LoadingIndicator/
   │   └── ErrorAlert/
   └── hooks/
       └── useQueryInterface.ts
   ```

2. Create type definitions file:
   ```
   frontend/src/views/QueryInterfaceView/types.ts
   ```

3. Set up basic component shells with TypeScript interfaces

**Time Estimate**: 2 hours

---

### Step 2: Implement Reusable UI Components
1. **Button Component**
   - Create base Button component with variants
   - Add loading state with spinner
   - Add icon support
   - Implement accessibility attributes
   - Test keyboard interactions

2. **TextArea Component**
   - Create multi-line input with auto-resize
   - Add character count integration
   - Implement maxLength enforcement
   - Add focus/blur states
   - Test accessibility

3. **LoadingIndicator Component**
   - Create animated spinner
   - Add stage-specific messages
   - Implement ARIA live region
   - Add elapsed time display (optional)

**Time Estimate**: 4 hours

---

### Step 3: Implement Query Form Section
1. **QueryForm Component**
   - Create form structure with semantic HTML
   - Integrate TextArea component
   - Add CharacterCount component
   - Implement form validation
   - Handle submit event
   - Add disabled state during submission

2. **CharacterCount Component**
   - Display current/max count
   - Add color coding based on thresholds
   - Implement ARIA announcements

3. **ExampleQuestions Component**
   - Create list of clickable examples
   - Handle example selection
   - Add disabled state
   - Style responsively

4. **Form Validation**
   - Implement validateQuery function
   - Add error message display
   - Integrate with submit handler

**Time Estimate**: 6 hours

---

### Step 4: Implement SQL Preview Section
1. **SqlPreviewSection Component**
   - Create section container
   - Add heading and layout
   - Integrate action buttons

2. **SqlPreview Component**
   - Install react-syntax-highlighter
   - Configure SQL highlighting theme
   - Add line numbers
   - Implement horizontal scroll
   - Test responsive behavior

3. **Copy to Clipboard**
   - Implement copy functionality
   - Add toast notification
   - Handle copy errors
   - Test on different browsers

4. **Execute Button**
   - Add prominent execute button
   - Implement disabled states
   - Add loading state during execution

**Time Estimate**: 5 hours

---

### Step 5: Implement Results Display
1. **ResultsSection Component**
   - Create section container
   - Add header with metrics
   - Integrate child components

2. **PerformanceMetrics Component**
   - Display generation time
   - Display execution time
   - Display row count
   - Add color coding
   - Format time values

3. **ResultsTable Component**
   - Create semantic table structure
   - Implement responsive column widths
   - Add alternating row colors
   - Handle null values
   - Add cell truncation with tooltips
   - Implement frozen first column on mobile
   - Add empty state

4. **Pagination Component**
   - Create Previous/Next buttons
   - Display page information
   - Implement disabled states
   - Add ARIA labels
   - Test keyboard navigation

**Time Estimate**: 6 hours

---

### Step 6: Implement Error Handling
1. **ErrorAlert Component**
   - Create alert container with ARIA role
   - Add icon based on error type
   - Display error message and details
   - Add action button
   - Implement dismissible functionality

2. **Error Message Mapping**
   - Create function to map error types to messages
   - Implement error detail extraction
   - Add recovery action suggestions

3. **Error Boundaries**
   - Set up React ErrorBoundary
   - Create fallback UI
   - Add error logging

**Time Estimate**: 3 hours

---

### Step 7: Implement State Management
1. **Create State Interface**
   - Define QueryInterfaceState type
   - Define all sub-types
   - Document state transitions

2. **Implement useState Hooks**
   - Set up main state object
   - Initialize default values
   - Create state update functions

3. **SessionStorage Integration**
   - Implement input persistence
   - Add restore on mount
   - Handle cleanup

4. **Create Custom Hook** (Optional)
   - Extract useQueryInterface hook
   - Organize state logic
   - Add action creators

**Time Estimate**: 4 hours

---

### Step 8: Implement API Integration
1. **Create API Service Functions**
   - Implement submitQuery function
   - Implement executeQuery function
   - Implement loadResults function
   - Implement exportCSV function

2. **Error Handling Wrapper**
   - Create fetch wrapper with error handling
   - Implement 401 redirect logic
   - Add retry logic for network errors
   - Handle different error status codes

3. **Authentication Integration**
   - Include session cookie in requests
   - Handle session expiration
   - Implement redirect on 401

**Time Estimate**: 5 hours

---

### Step 9: Wire Up User Interactions
1. **Query Submission Flow**
   - Connect form submit to API
   - Update loading states
   - Handle success response
   - Handle error response
   - Auto-scroll to SQL preview

2. **Execution Flow**
   - Connect execute button to API
   - Update loading states
   - Handle success response
   - Handle error response
   - Auto-scroll to results

3. **Pagination Flow**
   - Connect pagination buttons to API
   - Update table with new data
   - Handle loading state
   - Handle errors

4. **Export Flow**
   - Connect export button to API
   - Trigger file download
   - Show success toast
   - Handle truncation warning

5. **Retry/Reset Flow**
   - Implement "Try Again" functionality
   - Clear error state
   - Reset to input stage
   - Preserve user input for editing

**Time Estimate**: 6 hours

---

### Step 10: Add Accessibility Features
1. **Keyboard Navigation**
   - Test Tab order
   - Add skip links
   - Implement keyboard shortcuts (Ctrl+Enter)
   - Test with keyboard only

2. **Screen Reader Support**
   - Add ARIA labels
   - Implement live regions
   - Add role attributes
   - Test with screen reader

3. **Focus Management**
   - Focus on error messages
   - Focus on results after execution
   - Return focus after modal close

4. **Contrast and Colors**
   - Verify color contrast ratios
   - Ensure color is not sole indicator
   - Add icons to status indicators

**Time Estimate**: 4 hours

---

### Step 11: Styling and Responsive Design
1. **Desktop Styles**
   - Create base styles
   - Add component-specific styles
   - Implement color scheme
   - Add transitions and animations

2. **Mobile Responsive**
   - Add media queries for < 768px
   - Stack form elements vertically
   - Make table horizontally scrollable
   - Increase touch target sizes
   - Test on mobile devices

3. **Tablet Responsive**
   - Add media queries for 768px-1024px
   - Adjust spacing and sizing
   - Test on tablet devices

4. **Dark Mode** (Future)
   - Prepare CSS variables
   - Add theme switching logic

**Time Estimate**: 6 hours

---

### Step 12: Testing and Debugging
1. **Unit Tests**
   - Test validation functions
   - Test utility functions
   - Test error handling

2. **Component Tests**
   - Test form submission
   - Test button interactions
   - Test pagination
   - Test error display

3. **Integration Tests**
   - Test full query workflow
   - Test error recovery flows
   - Test pagination flow
   - Test export flow

4. **Manual Testing**
   - Test all user stories
   - Test edge cases
   - Test error scenarios
   - Test on different browsers

5. **Accessibility Testing**
   - Test with keyboard only
   - Test with screen reader
   - Verify ARIA attributes
   - Check color contrast

**Time Estimate**: 8 hours

---

### Step 13: Performance Optimization
1. **Code Splitting**
   - Lazy load heavy components
   - Split syntax highlighter library

2. **Memoization**
   - Memo expensive components (ResultsTable, SqlPreview)
   - Use useMemo for computed values
   - Use useCallback for event handlers

3. **Loading States**
   - Add skeleton screens
   - Optimize loading indicators

**Time Estimate**: 3 hours

---

### Step 14: Documentation and Cleanup
1. **Code Documentation**
   - Add JSDoc comments
   - Document component props
   - Document state structure

2. **README Updates**
   - Document view usage
   - Add screenshots
   - List known issues

3. **Code Cleanup**
   - Remove console.logs
   - Remove unused imports
   - Format code consistently
   - Run linter

**Time Estimate**: 2 hours

---

### Total Estimated Time: 64 hours

This estimate includes buffer time for debugging and iteration. Actual implementation time may vary based on developer experience and unforeseen challenges.

### Implementation Priority

**Phase 1 - Core Functionality** (40 hours):
- Steps 1-6: Basic UI and interactions
- Steps 7-9: State management and API integration
- Critical for MVP

**Phase 2 - Polish and Accessibility** (16 hours):
- Steps 10-11: Accessibility and styling
- Important for user experience

**Phase 3 - Testing and Optimization** (8 hours):
- Steps 12-14: Testing, optimization, documentation
- Essential for production readiness
