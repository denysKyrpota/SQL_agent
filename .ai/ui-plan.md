# UI Architecture for SQL AI Agent MVP

## 1. UI Structure Overview

The SQL AI Agent MVP follows a clean, focused architecture designed to minimize cognitive load while providing transparent access to AI-generated SQL queries. The interface uses a dual-layout system: a minimal layout for authentication and a persistent header layout for all authenticated views.

### Core Architecture Principles

- **Transparency First**: Users always see generated SQL before execution, building trust
- **Progressive Disclosure**: Information revealed step-by-step to avoid overwhelming users
- **Error Recovery**: Clear paths to retry after failures with helpful guidance
- **Audit Trail**: Complete history of queries maintains accountability
- **Role-Based Access**: Simple two-tier permission system (user/admin)

### Technical Foundation

- **Framework**: React with TypeScript for type safety
- **Routing**: React Router with protected route guards
- **State Management**: React Context for authentication, local state for forms
- **API Communication**: RESTful endpoints with session-based authentication
- **Styling Approach**: Component-based CSS with responsive breakpoints

### Security Architecture

- Session-based authentication with HttpOnly cookies
- 8-hour session expiration with automatic redirect
- Client-side validation before API calls
- SQL preview prevents blind execution
- Role-based rendering for admin features

## 2. View List

### 2.1 Login View

**View Path**: `/login`

**Main Purpose**: Authenticate users to access the SQL AI Agent system

**Key Information to Display**:
- Application logo and title
- Username input field
- Password input field
- Login button
- Error messages for failed authentication
- Session expiration notice (when redirected)

**Key View Components**:
- `LoginForm` - Main authentication form
- `InputField` - Reusable text input with validation
- `Button` - Primary action button
- `ErrorAlert` - Error message display

**Layout**: MinimalLayout (no header, centered card)

**UX Considerations**:
- Autofocus on username field for immediate input
- Enter key submits form from any field
- Clear error messages for invalid credentials vs. inactive accounts
- Remember session expiration message when redirected
- Disable submit button during authentication to prevent double-submission

**Accessibility**:
- Form labeled with aria-labelledby pointing to page title
- Input fields have associated labels with for/id attributes
- Error messages announced with role="alert"
- Tab order: username → password → login button
- Visible focus indicators on all interactive elements

**Security**:
- No password reveal toggle in MVP (security over convenience)
- Rate limiting feedback after 5 failed attempts
- Generic error messages to prevent username enumeration
- Client-side validation for empty fields
- HTTPS enforcement for credential transmission

**User Stories Addressed**: US-001, US-018

---

### 2.2 Query Interface View (Home)

**View Path**: `/` or `/query`

**Main Purpose**: Primary workspace for submitting natural language questions and executing queries

**Key Information to Display**:
- Multi-line textarea for natural language input
- Character count (0-5000)
- Example questions to guide users
- Two-stage loading indicator during SQL generation
- Generated SQL preview with syntax highlighting and line numbers
- Copy SQL button
- Execute query button
- Query results table (when executed)
- Pagination controls (if results exceed 500 rows)
- Row count and execution time
- CSV export button (when results available)
- Error messages with retry guidance

**Key View Components**:
- `QueryForm` - Natural language input form
- `ExampleQuestions` - Clickable example queries
- `LoadingIndicator` - Two-stage progress display
- `SqlPreview` - Syntax-highlighted SQL with line numbers
- `ResultsTable` - Data grid with responsive columns
- `Pagination` - Previous/Next navigation
- `ExportButton` - CSV download trigger
- `ErrorAlert` - Contextual error messages
- `MetadataDisplay` - Execution time and row count

**Layout**: MainLayout (persistent header with user info and logout)

**UX Considerations**:
- Preserve query text in sessionStorage to prevent data loss on refresh
- Clear button to reset form and sessionStorage
- Example questions clickable to populate textarea
- Progressive loading text: "Analyzing database schema..." → "Generating SQL query..."
- Disable form during generation/execution
- Execute button prominent but requires explicit click
- Smooth scroll to results after execution
- Empty state guidance when no results
- Truncation warning for exports exceeding 10,000 rows
- Optimistic UI updates with rollback on error

**Accessibility**:
- Textarea labeled "Enter your database question"
- Character count announced to screen readers at 4000, 4500, 4900, 5000
- Loading states announced with aria-live="polite"
- SQL preview in code element with aria-label="Generated SQL query"
- Copy button announces "Copied!" confirmation
- Execute button disabled state clearly indicated
- Results table has proper thead/tbody structure
- Column headers have scope="col"
- Pagination announces current page and total pages

**Security**:
- Input sanitization before API submission
- SQL preview prevents blind execution
- Execute requires explicit confirmation
- No execution of queries without preview
- Client-side validation for empty/whitespace-only input
- XSS prevention via React's default escaping

**User Stories Addressed**: US-003, US-004, US-005, US-006, US-007, US-008, US-009, US-010, US-011, US-015, US-016, US-021, US-022, US-023

**State Management**:
```
Local State:
- naturalLanguageQuery: string
- queryId: number | null
- generatedSql: string | null
- status: 'idle' | 'generating' | 'generated' | 'executing' | 'success' | 'error'
- results: QueryResults | null
- currentPage: number
- errorMessage: string | null
- generationTimeMs: number | null
- executionTimeMs: number | null

SessionStorage:
- queryInputText: string (persistence across refreshes)
```

**API Integration**:
1. POST /queries - Submit natural language query
2. POST /queries/{id}/execute - Execute generated SQL
3. GET /queries/{id}/results?page=N - Fetch paginated results
4. GET /queries/{id}/export - Download CSV

---

### 2.3 Query History View

**View Path**: `/history`

**Main Purpose**: Review past queries and re-run previous questions

**Key Information to Display**:
- List of previous queries in reverse chronological order
- For each query:
  - Natural language question (truncated if long)
  - Status badge (success, failed, timeout, not executed)
  - Timestamp (relative: "2 hours ago", absolute on hover)
  - Generated SQL (expandable/collapsible)
  - Re-run button
  - View results button (if executed successfully)
- Pagination controls (20 queries per page)
- Status filter dropdown (all, success, failed, timeout, not executed)
- Empty state message for new users

**Key View Components**:
- `QueryHistoryList` - Scrollable list container
- `QueryHistoryItem` - Individual query card
- `StatusBadge` - Color-coded status indicator
- `ExpandableSection` - Collapsible SQL display
- `Pagination` - Page navigation
- `FilterDropdown` - Status filter
- `EmptyState` - No queries message

**Layout**: MainLayout

**UX Considerations**:
- Read-only interface (no delete in MVP)
- Click to expand/collapse SQL preview
- Re-run creates new query attempt (doesn't modify original)
- Status filtering updates URL query params for bookmarkability
- Infinite scroll consideration (deferred to Phase 2)
- Highlight recently executed queries (last 5 minutes)
- Skeleton loading for initial page load
- Optimistic re-run navigation to Query Interface

**Accessibility**:
- List semantics with ul/li elements
- Each item has heading with query text
- Status badges have aria-label with full status text
- Expand/collapse buttons clearly labeled
- Keyboard navigation: Tab through items, Enter to expand/re-run
- Focus management when returning from Query Interface
- Announced updates when filtering

**Security**:
- Non-admin users see only their own queries
- Admin users see all queries (future: add user filter)
- No delete capability prevents audit trail tampering
- SQL display is read-only (no editing)

**User Stories Addressed**: US-012, US-013

**State Management**:
```
Local State:
- queries: QueryHistoryItem[]
- currentPage: number
- totalPages: number
- statusFilter: string | null
- expandedQueryIds: Set<number>
- loading: boolean

URL Query Params:
- page: number
- status: string | null
```

**API Integration**:
1. GET /queries?page=N&status=filter - Fetch query history
2. POST /queries/{id}/rerun - Re-run historical query

---

### 2.4 Query Detail View

**View Path**: `/query/{id}`

**Main Purpose**: View complete details of a specific query attempt

**Key Information to Display**:
- Natural language question
- Generated SQL with syntax highlighting and line numbers
- Status badge
- Timestamps:
  - Created at
  - Generated at
  - Executed at (if applicable)
- Performance metrics:
  - SQL generation time
  - Query execution time
- Error message (if failed)
- Results table (if executed successfully)
- Pagination controls
- CSV export button
- Re-run button
- Link to original query (if this is a re-run)
- Breadcrumb: History > Query #ID

**Key View Components**:
- `QueryDetailHeader` - Metadata and status
- `SqlPreview` - Syntax-highlighted SQL
- `ResultsTable` - Data grid
- `Pagination` - Page navigation
- `ExportButton` - CSV download
- `ErrorAlert` - Error display
- `PerformanceMetrics` - Timing information
- `Breadcrumb` - Navigation trail

**Layout**: MainLayout

**UX Considerations**:
- Single source of truth for query details
- Deep linkable for sharing query results
- Back to history button for easy navigation
- Execute button if status is 'not_executed'
- Re-run creates new attempt and navigates to Query Interface
- Performance metrics help users understand query complexity
- Lineage display if query is a re-run

**Accessibility**:
- Structured heading hierarchy (h1: Question, h2: SQL, Results)
- Definition list for metadata (dt/dd pairs)
- Performance metrics in accessible format
- Focus management when navigating back

**Security**:
- Authorization check: user owns query or is admin
- 403 redirect if unauthorized
- No modification capability

**User Stories Addressed**: US-004, US-006, US-007, US-008, US-013, US-022, US-023

**State Management**:
```
Local State:
- query: QueryDetail | null
- currentResultsPage: number
- loading: boolean
- error: string | null
```

**API Integration**:
1. GET /queries/{id} - Fetch query details
2. GET /queries/{id}/results?page=N - Fetch results page
3. POST /queries/{id}/execute - Execute if not yet executed
4. POST /queries/{id}/rerun - Re-run query
5. GET /queries/{id}/export - Export CSV

---

### 2.5 Admin Schema Management View

**View Path**: `/admin/schema`

**Main Purpose**: Admin-only interface for refreshing database schema cache

**Key Information to Display**:
- Current schema snapshot information:
  - Last loaded timestamp
  - Source hash (for change detection)
  - Table count
  - Column count
- Refresh button
- Refresh status indicator
- Success/error message after refresh
- Recent schema refresh history (last 5)

**Key View Components**:
- `SchemaSnapshotCard` - Current schema info
- `RefreshButton` - Trigger schema reload
- `StatusIndicator` - Loading/success/error state
- `RefreshHistory` - Recent refresh log
- `AdminBreadcrumb` - Navigation trail

**Layout**: MainLayout with admin badge

**UX Considerations**:
- Visible only to admin users
- Refresh button disabled during operation
- Loading indicator during refresh (may take 10-30 seconds)
- Success message with new snapshot details
- Error message with troubleshooting guidance
- Confirmation dialog before refresh (optional safety measure)

**Accessibility**:
- Admin-only content announced to screen readers
- Refresh button clearly labeled with current status
- Status updates announced with aria-live
- Keyboard accessible throughout

**Security**:
- Role check: admin only
- 403 redirect if non-admin attempts access
- No direct schema editing (read-only view)
- Refresh operation logged with user attribution

**User Stories Addressed**: US-014

**State Management**:
```
Local State:
- currentSnapshot: SchemaSnapshot | null
- refreshHistory: SchemaSnapshot[]
- refreshing: boolean
- message: { type: 'success' | 'error', text: string } | null
```

**API Integration**:
1. POST /admin/schema/refresh - Trigger schema reload

---

### 2.6 Admin Knowledge Base Management View

**View Path**: `/admin/knowledge-base`

**Main Purpose**: Admin-only interface for reloading knowledge base examples

**Key Information to Display**:
- Current knowledge base statistics:
  - Number of examples loaded
  - Last reload timestamp
  - Total embeddings count
- Reload button
- Reload status indicator
- Success/error message after reload
- File parsing errors (if any)

**Key View Components**:
- `KnowledgeBaseStatsCard` - Current KB info
- `ReloadButton` - Trigger KB reload
- `StatusIndicator` - Loading/success/error state
- `ErrorList` - File parsing issues
- `AdminBreadcrumb` - Navigation trail

**Layout**: MainLayout with admin badge

**UX Considerations**:
- Visible only to admin users
- Reload button disabled during operation
- Loading indicator during reload (embedding generation may take time)
- Success message with statistics
- Error list for problematic .sql files
- Guidance on fixing file format issues

**Accessibility**:
- Admin-only content announced to screen readers
- Reload button clearly labeled
- Status updates announced
- Error list keyboard navigable

**Security**:
- Role check: admin only
- 403 redirect if non-admin
- No direct file editing through UI (manual server file management)
- Reload operation logged

**User Stories Addressed**: Knowledge base management (implied in admin functions)

**State Management**:
```
Local State:
- kbStats: { exampleCount: number, lastReload: string, embeddingCount: number } | null
- reloading: boolean
- message: { type: 'success' | 'error', text: string } | null
- fileErrors: { filename: string, error: string }[]
```

**API Integration**:
1. POST /admin/kb/reload - Trigger knowledge base reload

---

### 2.7 Admin Metrics View

**View Path**: `/admin/metrics`

**Main Purpose**: Admin-only dashboard for system usage metrics

**Key Information to Display**:
- Time period selector (last 4 weeks, 8 weeks, etc.)
- Weekly metrics table:
  - Week start date
  - Total query attempts
  - Queries executed
  - Successful executions
  - Success rate percentage
  - Acceptance rate percentage
- Per-user breakdown (expandable)
- Summary statistics:
  - Total attempts
  - Overall success rate
  - Overall acceptance rate
  - Average queries per user per week
  - Active user count

**Key View Components**:
- `MetricsTimePeriodSelector` - Week range picker
- `MetricsSummaryCard` - High-level statistics
- `MetricsTable` - Weekly breakdown
- `UserMetricsBreakdown` - Per-user details
- `MetricsChart` - Simple trend visualization (optional)

**Layout**: MainLayout with admin badge

**UX Considerations**:
- Simple tabular display for MVP
- No real-time updates (refresh to see latest)
- Export metrics as CSV (future enhancement)
- Color-coded success rates (red <70%, yellow 70-85%, green >85%)

**Accessibility**:
- Data table with proper semantics
- Summary statistics as definition list
- Chart has text alternative if implemented

**Security**:
- Role check: admin only
- 403 redirect if non-admin
- No PII exposure in metrics view

**User Stories Addressed**: Admin metrics (success criteria tracking)

**State Management**:
```
Local State:
- weekCount: number
- metrics: WeeklyMetric[]
- summary: MetricsSummary | null
- loading: boolean
```

**API Integration**:
1. GET /admin/metrics?weeks=N - Fetch usage metrics

---

### 2.8 Error Views

#### 2.8.1 404 Not Found

**View Path**: `*` (catch-all route)

**Main Purpose**: Handle invalid URLs gracefully

**Key Information to Display**:
- 404 error message
- Explanation: "The page you're looking for doesn't exist"
- Navigation suggestions:
  - Link to Query Interface
  - Link to History
  - Link to Login (if not authenticated)

**Layout**: Depends on authentication state (MinimalLayout or MainLayout)

---

#### 2.8.2 403 Forbidden

**View Path**: N/A (inline component)

**Main Purpose**: Handle unauthorized access attempts

**Key Information to Display**:
- 403 error message
- Explanation: "You don't have permission to access this resource"
- Suggestions:
  - Contact admin if you believe this is an error
  - Return to Query Interface

**Layout**: MainLayout (user is authenticated)

---

#### 2.8.3 Session Expired

**View Path**: N/A (redirect to login)

**Main Purpose**: Handle session expiration gracefully

**Behavior**:
- Redirect to /login
- Display message: "Your session has expired. Please log in again."
- Clear authentication context

---

## 3. User Journey Map

### 3.1 Primary User Journey: First-Time Query Submission

**Actor**: Non-technical business analyst (Sarah)

**Goal**: Get sales data for last quarter without knowing SQL

**Journey Steps**:

1. **Entry Point**: Sarah navigates to application URL
   - System redirects to `/login` (not authenticated)

2. **Authentication** (Login View):
   - Sarah enters username and password
   - Clicks "Log In" button
   - System validates credentials (POST /auth/login)
   - System sets session cookie and redirects to `/`

3. **Query Interface Landing** (Query Interface View):
   - Sarah sees welcome message with her username in header
   - Notices example questions: "What were our top 10 customers by revenue last quarter?"
   - Clicks example to populate textarea

4. **Query Submission**:
   - Sarah reviews the question in textarea
   - Clicks "Generate SQL" button
   - System shows loading indicator: "Analyzing database schema..."
   - Text changes to: "Generating SQL query..."
   - POST /queries API call in progress

5. **SQL Preview**:
   - Generated SQL appears with syntax highlighting and line numbers
   - Sarah reviews the query (sees JOIN between customers and orders tables)
   - Notices "Copy" and "Execute Query" buttons
   - Gains confidence from seeing transparent SQL

6. **Query Execution**:
   - Sarah clicks "Execute Query"
   - System shows "Running query..." indicator
   - POST /queries/{id}/execute API call
   - Loading indicator disappears after 3 seconds

7. **Results Display**:
   - Results table appears showing 10 customers with revenue figures
   - Sarah sees "Execution time: 2.3s" and "10 rows returned"
   - Notices CSV export button

8. **Export**:
   - Sarah clicks "Export CSV"
   - Browser downloads `query_42_20250126_150730.csv`
   - Toast notification: "CSV exported successfully"
   - Sarah opens in Excel to share with team

9. **Journey Completion**:
   - Sarah successfully obtained data without writing SQL
   - Total time: ~5 minutes (vs. previous 2-day turnaround)

**Pain Points Addressed**:
- ✅ No SQL knowledge required
- ✅ No dependency on technical team
- ✅ Immediate results instead of ticket waiting
- ✅ Transparent process builds trust
- ✅ Easy data export for sharing

---

### 3.2 Secondary User Journey: Query Refinement After Error

**Actor**: Business analyst (Mike)

**Goal**: Refine a query that failed to execute

**Journey Steps**:

1. **Starting Point**: Mike is on Query Interface with failed query
   - Error message: "Query failed to execute. The generated SQL may be invalid."
   - Database error: "Column 'customer_address' does not exist"

2. **Understanding Error**:
   - Mike reads error message
   - Realizes the column name might be wrong
   - Notices "Try Again" button

3. **Query Refinement**:
   - Mike clicks "Try Again"
   - Form resets, previous question cleared
   - Mike rephrases: "What were our top 10 customers by revenue last quarter?" (removes address reference)
   - Submits new query

4. **Successful Execution**:
   - New SQL generated without referencing non-existent column
   - Mike executes query
   - Results display successfully

5. **History Review**:
   - Mike navigates to History view to see both attempts
   - Notes that first query failed, second succeeded
   - Learns from comparison

**Pain Points Addressed**:
- ✅ Clear error guidance
- ✅ Easy retry path
- ✅ Learning from failures
- ✅ Audit trail of attempts

---

### 3.3 Power User Journey: Re-running Historical Query

**Actor**: Data analyst (Jessica)

**Goal**: Re-run a successful query from last month to get updated data

**Journey Steps**:

1. **Navigation**: Jessica clicks "History" in header
   - Lands on `/history`
   - Sees list of past queries

2. **Finding Query**:
   - Scrolls through history (most recent first)
   - Remembers query was about monthly revenue
   - Uses browser find (Ctrl+F) to search for "monthly"
   - Locates query from 4 weeks ago

3. **Expanding Details**:
   - Clicks to expand SQL preview
   - Reviews query to confirm it's the right one
   - Sees status badge: "Success"

4. **Re-running**:
   - Clicks "Re-run" button
   - System creates new query attempt (POST /queries/{id}/rerun)
   - Redirects to Query Interface (`/`)
   - New SQL generated (may differ due to knowledge base updates)

5. **Execution and Comparison**:
   - Reviews new SQL
   - Executes query
   - Gets updated data with current month included
   - Exports CSV for monthly report

**Pain Points Addressed**:
- ✅ Reusable query patterns
- ✅ Updated data with same question
- ✅ Complete audit trail
- ✅ Time savings (no re-typing)

---

### 3.4 Admin Journey: Schema Update

**Actor**: Admin user (Tom)

**Goal**: Refresh schema cache after database schema changes

**Journey Steps**:

1. **Context**: Database team added new tables for product catalog

2. **Navigation**: Tom logs in and clicks "Admin" in header
   - Dropdown shows: Schema Management, Knowledge Base, Metrics
   - Selects "Schema Management"
   - Lands on `/admin/schema`

3. **Current State Review**:
   - Sees current schema loaded 3 days ago
   - Notes table count: 45 tables
   - Schema hash: abc123def

4. **Refresh Trigger**:
   - Clicks "Refresh Schema" button
   - Confirmation dialog: "This will reload schema from JSON files. Continue?"
   - Clicks "Confirm"
   - Loading indicator appears

5. **Completion**:
   - After 15 seconds, success message appears
   - New schema details: 52 tables (7 new tables detected)
   - New hash: def456ghi
   - Loaded at timestamp shows current time

6. **Verification**:
   - Tom navigates to Query Interface
   - Submits test question about new product catalog tables
   - SQL generated successfully includes new tables
   - Confirms schema update worked

**Pain Points Addressed**:
- ✅ Simple admin operation
- ✅ No application restart needed
- ✅ Clear success confirmation
- ✅ Immediate availability

---

### 3.5 Edge Case Journey: Session Expiration

**Actor**: User (Karen)

**Goal**: Submit a query after 8-hour session expires

**Journey Steps**:

1. **Context**: Karen logged in at 9 AM, now it's 5:30 PM
   - Session expired at 5 PM (8 hours)
   - Karen still has browser tab open

2. **Interaction Attempt**:
   - Karen types query and clicks "Generate SQL"
   - API returns 401 Unauthorized
   - Axios interceptor catches 401

3. **Automatic Redirect**:
   - System clears authentication context
   - Redirects to `/login`
   - Shows message: "Your session has expired. Please log in again."
   - Query text saved in sessionStorage (not lost)

4. **Re-authentication**:
   - Karen logs in again
   - Redirects to `/` (Query Interface)
   - Previous query text restored from sessionStorage
   - Karen clicks "Generate SQL" again
   - Successfully generates SQL

**Pain Points Addressed**:
- ✅ Graceful session expiration handling
- ✅ Data preservation (no lost work)
- ✅ Clear messaging
- ✅ Simple re-authentication

---

## 4. Layout and Navigation Structure

### 4.1 Layout System

#### MinimalLayout

**Used For**: Unauthenticated views (Login)

**Structure**:
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│          ┌─────────────┐           │
│          │             │           │
│          │   Content   │           │
│          │             │           │
│          └─────────────┘           │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

**Characteristics**:
- Centered content card
- No header or navigation
- Minimal branding
- Responsive: full width on mobile, max-width 400px on desktop

---

#### MainLayout

**Used For**: All authenticated views

**Structure**:
```
┌─────────────────────────────────────────────────┐
│  Header                                         │
│  Logo | Query | History | [Admin▼] | User▼    │
├─────────────────────────────────────────────────┤
│                                                 │
│                                                 │
│              Content Area                       │
│                                                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Header Components**:
- **Logo/Brand**: Links to `/` (Query Interface)
- **Primary Navigation**: Query | History
- **Admin Dropdown** (admin only): Schema Management | Knowledge Base | Metrics
- **User Dropdown**: Username | Role Badge | Logout

**Characteristics**:
- Persistent header across all authenticated views
- Sticky header on scroll (optional)
- Responsive: Hamburger menu on mobile, full nav on desktop
- Active route highlighted

---

### 4.2 Navigation Structure

#### Primary Navigation

**Available to All Users**:
1. **Query** (`/`)
   - Default landing page after login
   - Primary action hub
   - Always accessible

2. **History** (`/history`)
   - Access past queries
   - Re-run functionality
   - Audit trail

#### Admin Navigation

**Available to Admin Role Only**:
1. **Schema Management** (`/admin/schema`)
   - Refresh database schema
   - View current snapshot

2. **Knowledge Base** (`/admin/knowledge-base`)
   - Reload example queries
   - View KB statistics

3. **Metrics** (`/admin/metrics`)
   - Usage statistics
   - Success rate tracking

#### User Menu

**Available to All Users**:
- **Username Display**: Shows logged-in user
- **Role Badge**: "Admin" or "User"
- **Logout**: Clears session and redirects to login

---

### 4.3 Navigation Patterns

#### Breadcrumbs

Used on detail views:
- Query Detail: `History > Query #42`
- Admin views: `Admin > Schema Management`

**Implementation**:
- Clickable segments
- Current page not clickable
- Collapsed on mobile (show only parent)

---

#### In-Page Navigation

Query Interface has multiple sections:
1. Query Form (always visible)
2. SQL Preview (after generation)
3. Results (after execution)

**Scroll Behavior**:
- Auto-scroll to SQL preview after generation
- Auto-scroll to results after execution
- Smooth scrolling with focus management

---

### 4.4 Route Protection

#### Protected Routes

All authenticated routes use `ProtectedRoute` wrapper:
- Checks authentication context
- Redirects to `/login` if not authenticated
- Preserves intended destination for post-login redirect

#### Admin Routes

Admin-only routes use `AdminRoute` wrapper:
- Checks authentication context
- Checks admin role
- Returns 403 error if non-admin attempts access

#### Route Configuration

```
Public Routes:
- /login

Protected Routes (authenticated):
- / (Query Interface)
- /query (alias for /)
- /history
- /query/:id (Query Detail)

Admin Routes (admin role):
- /admin/schema
- /admin/knowledge-base
- /admin/metrics

Error Routes:
- /403 (Forbidden)
- * (404 Not Found)
```

---

### 4.5 Navigation State Management

#### Active Route Highlighting

- Current route highlighted in header navigation
- CSS class: `active` or `nav-active`
- Visual indicator: underline, background color, or bold text

#### Navigation History

- Browser back button support (React Router handles this)
- Breadcrumb navigation for hierarchical views
- "Back to History" links on detail views

#### Deep Linking

All views support deep linking:
- `/query/42` - Direct link to query detail
- `/history?page=2&status=success` - Bookmarkable filtered history
- `/admin/metrics?weeks=8` - Admin metrics with time period

---

## 5. Key Components

### 5.1 Form Components

#### InputField

**Purpose**: Reusable text input with validation and error display

**Props**:
- `label`: string - Field label
- `type`: 'text' | 'password' | 'email' - Input type
- `value`: string - Current value
- `onChange`: (value: string) => void - Change handler
- `error`: string | null - Error message
- `required`: boolean - Required field indicator
- `placeholder`: string - Placeholder text
- `autoFocus`: boolean - Auto-focus on mount
- `disabled`: boolean - Disabled state

**Features**:
- Associated label with htmlFor/id
- Error message display with role="alert"
- Required indicator (*)
- Disabled state styling
- Focus styles for accessibility

**Used In**: Login Form, Admin forms

---

#### TextArea

**Purpose**: Multi-line text input for natural language queries

**Props**:
- `label`: string - Field label
- `value`: string - Current value
- `onChange`: (value: string) => void - Change handler
- `maxLength`: number - Character limit (5000)
- `placeholder`: string - Placeholder text
- `rows`: number - Initial row count
- `disabled`: boolean - Disabled state
- `error`: string | null - Error message

**Features**:
- Character count display (live update)
- Auto-resize based on content
- Character limit enforcement
- Warning at 90% capacity (4500 chars)
- Copy/paste support
- Undo/redo support

**Used In**: Query Interface

---

#### Button

**Purpose**: Reusable action button with variants

**Props**:
- `children`: ReactNode - Button content
- `onClick`: () => void - Click handler
- `variant`: 'primary' | 'secondary' | 'danger' - Visual style
- `disabled`: boolean - Disabled state
- `loading`: boolean - Loading state with spinner
- `type`: 'button' | 'submit' - Button type
- `icon`: ReactNode - Optional icon
- `fullWidth`: boolean - Full width button

**Features**:
- Loading spinner replaces content when loading=true
- Disabled state prevents clicks
- Icon support (left-aligned)
- Keyboard accessible (Enter/Space)
- Focus visible indicator

**Used In**: All forms, action buttons throughout app

---

### 5.2 Display Components

#### SqlPreview

**Purpose**: Syntax-highlighted SQL display with line numbers

**Props**:
- `sql`: string - SQL code to display
- `showLineNumbers`: boolean - Show line numbers (default: true)
- `showCopyButton`: boolean - Show copy button (default: true)
- `onCopy`: () => void - Copy callback

**Features**:
- Syntax highlighting (Prism.js or react-syntax-highlighter)
- Line numbers for error reference
- Copy to clipboard functionality
- Copy confirmation toast
- Responsive: horizontal scroll on mobile
- Code block semantics (pre/code elements)

**Used In**: Query Interface, Query Detail, History View

---

#### ResultsTable

**Purpose**: Data grid for query results with responsive columns

**Props**:
- `columns`: string[] - Column names
- `rows`: any[][] - Row data
- `totalRows`: number - Total row count
- `currentPage`: number - Current page number
- `onPageChange`: (page: number) => void - Page change handler

**Features**:
- Responsive column widths based on data type detection:
  - Narrow: IDs, numbers (100px)
  - Medium: Dates, short text (150px)
  - Wide: Long text (200-300px)
- Horizontal scroll on mobile
- Frozen first column on mobile
- Proper table semantics (thead, tbody, th, td)
- Alternating row colors for readability
- Empty state message
- Cell truncation with title attribute for hover

**Used In**: Query Interface, Query Detail

---

#### Pagination

**Purpose**: Page navigation for large result sets

**Props**:
- `currentPage`: number - Current page
- `totalPages`: number - Total page count
- `onPageChange`: (page: number) => void - Page change handler
- `pageSize`: number - Rows per page (display only)

**Features**:
- Previous/Next buttons
- Disable Previous on page 1
- Disable Next on last page
- Current page and total count display: "Page 2 of 5"
- Keyboard navigation (Arrow keys)
- Screen reader announcements

**Used In**: Query Interface, Query Detail, History View

---

#### StatusBadge

**Purpose**: Color-coded status indicator

**Props**:
- `status`: 'success' | 'failed_generation' | 'failed_execution' | 'timeout' | 'not_executed'
- `size`: 'small' | 'medium' | 'large'

**Features**:
- Color coding:
  - success: Green
  - failed_*: Red
  - timeout: Orange
  - not_executed: Gray
- Accessible text labels
- Icon support (checkmark, X, clock, etc.)
- Tooltip with full status description

**Used In**: History View, Query Detail

---

### 5.3 Feedback Components

#### LoadingIndicator

**Purpose**: Two-stage loading display for SQL generation

**Props**:
- `stage`: 'schema' | 'generation' | 'execution'
- `message`: string (optional override)

**Features**:
- Animated spinner or progress indicator
- Stage-specific messages:
  - schema: "Analyzing database schema..."
  - generation: "Generating SQL query..."
  - execution: "Running query..."
- Screen reader announcements with aria-live="polite"
- Overlay mode for blocking operations

**Used In**: Query Interface

---

#### ErrorAlert

**Purpose**: Contextual error message display

**Props**:
- `message`: string - Error message
- `type`: 'error' | 'warning' | 'info'
- `dismissible`: boolean - Show close button
- `onDismiss`: () => void - Dismiss handler
- `action`: { label: string, onClick: () => void } - Optional action button

**Features**:
- Color-coded by type (red for error, yellow for warning, blue for info)
- Icon support (error icon, warning icon, info icon)
- Dismissible with X button
- Optional action button ("Try Again")
- Screen reader announcement with role="alert"
- Auto-dismiss after timeout (configurable)

**Used In**: All views for error handling

---

#### Toast

**Purpose**: Temporary notification for non-critical feedback

**Props**:
- `message`: string - Notification message
- `type`: 'success' | 'error' | 'info'
- `duration`: number - Display duration in ms (default: 3000)

**Features**:
- Positioned top-right or bottom-center
- Auto-dismiss after duration
- Queue system for multiple toasts
- Slide-in animation
- Dismissible with click or swipe
- Screen reader announcement

**Used In**: Copy confirmation, CSV export confirmation, admin actions

---

#### EmptyState

**Purpose**: Guidance when no content is available

**Props**:
- `message`: string - Primary message
- `description`: string - Detailed explanation
- `action`: { label: string, onClick: () => void } - Optional CTA

**Features**:
- Icon or illustration
- Centered layout
- Call-to-action button
- Helpful guidance (not just "No results")

**Used In**: History View (no queries), Results (no rows)

---

### 5.4 Navigation Components

#### Header

**Purpose**: Persistent navigation bar for authenticated views

**Features**:
- Logo/brand linking to home
- Primary navigation links
- Admin dropdown (conditional)
- User dropdown
- Active route highlighting
- Responsive: hamburger menu on mobile
- Sticky positioning (optional)

**Used In**: MainLayout

---

#### Breadcrumb

**Purpose**: Hierarchical navigation trail

**Props**:
- `segments`: { label: string, path: string | null }[]

**Features**:
- Clickable segments (except current)
- Separator (/ or >)
- Truncation on mobile
- Accessible navigation semantics

**Used In**: Query Detail, Admin views

---

#### UserMenu

**Purpose**: User account dropdown in header

**Features**:
- Username display
- Role badge
- Logout button
- Dropdown positioning
- Click-outside to close
- Keyboard navigation (Tab, Arrow keys, Escape)

**Used In**: Header component

---

### 5.5 Layout Components

#### MinimalLayout

**Purpose**: Centered layout for authentication

**Features**:
- Centered content card
- Responsive max-width
- No header or navigation
- Background styling

**Used In**: Login View

---

#### MainLayout

**Purpose**: Standard layout with persistent header

**Features**:
- Header component
- Content area with max-width
- Responsive padding
- Footer (optional)

**Used In**: All authenticated views

---

### 5.6 Specialized Components

#### ExampleQuestions

**Purpose**: Display clickable example queries

**Props**:
- `examples`: string[] - List of example questions
- `onSelect`: (example: string) => void - Selection handler

**Features**:
- List or grid layout
- Clickable to populate form
- Icon indicating clickability
- Truncation for long examples
- Responsive: stack on mobile

**Used In**: Query Interface

---

#### PerformanceMetrics

**Purpose**: Display query performance information

**Props**:
- `generationTimeMs`: number | null - SQL generation time
- `executionTimeMs`: number | null - Query execution time
- `rowCount`: number | null - Total rows returned

**Features**:
- Formatted time display (ms, s)
- Color coding for performance (green <5s, yellow 5-30s, red >30s)
- Icon indicators
- Tooltip with detailed breakdown

**Used In**: Query Interface, Query Detail

---

#### ExpandableSection

**Purpose**: Collapsible content container

**Props**:
- `title`: string - Section title
- `children`: ReactNode - Content
- `defaultExpanded`: boolean - Initial state

**Features**:
- Expand/collapse animation
- Chevron icon rotation
- Keyboard navigation (Enter/Space to toggle)
- Accessible button semantics
- aria-expanded attribute

**Used In**: History View (SQL preview)

---

#### FilterDropdown

**Purpose**: Status filter for query history

**Props**:
- `value`: string | null - Selected filter
- `options`: { label: string, value: string }[] - Filter options
- `onChange`: (value: string | null) => void - Change handler

**Features**:
- "All" option to clear filter
- Keyboard navigation
- Search within dropdown (optional)
- Accessible select semantics

**Used In**: History View

---

### 5.7 Utility Components

#### ProtectedRoute

**Purpose**: Route wrapper for authentication

**Features**:
- Check authentication context
- Redirect to login if not authenticated
- Preserve intended destination
- Loading state while checking auth

**Used In**: Route configuration

---

#### AdminRoute

**Purpose**: Route wrapper for admin-only access

**Features**:
- Check authentication context
- Check admin role
- Show 403 if non-admin
- Redirect to login if not authenticated

**Used In**: Admin route configuration

---

#### ErrorBoundary

**Purpose**: Catch React errors and display fallback UI

**Features**:
- Global error catching
- User-friendly error message
- "Refresh page" action
- Error logging (console or external service)
- Doesn't catch API errors (handled separately)

**Used In**: Root app wrapper

---

### 5.8 Component Hierarchy

```
App
├── ErrorBoundary
│   ├── AuthProvider (Context)
│   │   ├── Router
│   │   │   ├── MinimalLayout
│   │   │   │   └── LoginView
│   │   │   │       └── LoginForm
│   │   │   │           ├── InputField
│   │   │   │           └── Button
│   │   │   │
│   │   │   ├── MainLayout
│   │   │   │   ├── Header
│   │   │   │   │   ├── UserMenu
│   │   │   │   │   └── Breadcrumb
│   │   │   │   │
│   │   │   │   └── Content (Route-specific)
│   │   │   │       │
│   │   │   │       ├── QueryInterfaceView
│   │   │   │       │   ├── QueryForm
│   │   │   │       │   │   ├── TextArea
│   │   │   │       │   │   ├── ExampleQuestions
│   │   │   │       │   │   └── Button
│   │   │   │       │   ├── LoadingIndicator
│   │   │   │       │   ├── SqlPreview
│   │   │   │       │   ├── ResultsTable
│   │   │   │       │   ├── Pagination
│   │   │   │       │   ├── PerformanceMetrics
│   │   │   │       │   └── ErrorAlert
│   │   │   │       │
│   │   │   │       ├── QueryHistoryView
│   │   │   │       │   ├── FilterDropdown
│   │   │   │       │   ├── QueryHistoryList
│   │   │   │       │   │   └── QueryHistoryItem
│   │   │   │       │   │       ├── StatusBadge
│   │   │   │       │   │       ├── ExpandableSection
│   │   │   │       │   │       │   └── SqlPreview
│   │   │   │       │   │       └── Button
│   │   │   │       │   ├── Pagination
│   │   │   │       │   └── EmptyState
│   │   │   │       │
│   │   │   │       ├── QueryDetailView
│   │   │   │       │   ├── QueryDetailHeader
│   │   │   │       │   │   ├── StatusBadge
│   │   │   │       │   │   └── PerformanceMetrics
│   │   │   │       │   ├── SqlPreview
│   │   │   │       │   ├── ResultsTable
│   │   │   │       │   ├── Pagination
│   │   │   │       │   └── ErrorAlert
│   │   │   │       │
│   │   │   │       └── Admin Views
│   │   │   │           ├── AdminSchemaView
│   │   │   │           │   ├── SchemaSnapshotCard
│   │   │   │           │   ├── RefreshButton
│   │   │   │           │   └── StatusIndicator
│   │   │   │           │
│   │   │   │           ├── AdminKnowledgeBaseView
│   │   │   │           │   ├── KnowledgeBaseStatsCard
│   │   │   │           │   ├── ReloadButton
│   │   │   │           │   └── ErrorList
│   │   │   │           │
│   │   │   │           └── AdminMetricsView
│   │   │   │               ├── MetricsTimePeriodSelector
│   │   │   │               ├── MetricsSummaryCard
│   │   │   │               └── MetricsTable
│   │   │   │
│   │   │   └── Toast (Global)
```

---

## 6. User Story Mapping to UI Elements

### Authentication Stories

**US-001: User Login**
- View: Login View (`/login`)
- Components: LoginForm, InputField, Button
- Features: Username/password fields, submit button, error display

**US-002: User Logout**
- Component: UserMenu (in Header)
- Features: Logout button, session clear, redirect to login

**US-018: Handle Session Expiration**
- Mechanism: API interceptor
- Features: Auto-redirect to login, session expired message, query preservation

---

### Core Query Workflow Stories

**US-003: Submit Natural Language Query**
- View: Query Interface View (`/`)
- Components: QueryForm, TextArea, Button
- Features: Multi-line input, character count, submit button, loading state

**US-004: View Generated SQL**
- View: Query Interface View (`/`)
- Components: SqlPreview, Button (Copy, Execute)
- Features: Syntax highlighting, line numbers, copy functionality

**US-005: Execute Confirmed Query**
- View: Query Interface View (`/`)
- Components: Button (Execute), LoadingIndicator
- Features: Explicit execute button, execution loading state, timeout handling

**US-006: View Query Results**
- View: Query Interface View (`/`)
- Components: ResultsTable, PerformanceMetrics
- Features: Tabular display, row count, execution time, empty state

**US-007: Navigate Result Pages**
- View: Query Interface View (`/`), Query Detail View (`/query/{id}`)
- Components: Pagination
- Features: Previous/Next buttons, page count display, disable on boundaries

**US-008: Export Results to CSV**
- View: Query Interface View (`/`), Query Detail View (`/query/{id}`)
- Components: Button (Export), Toast
- Features: Export button, CSV download, truncation warning, confirmation toast

**US-009: Retry After Failure**
- View: Query Interface View (`/`)
- Components: ErrorAlert, Button (Try Again)
- Features: Try Again button, form reset, new query submission

---

### Error Handling Stories

**US-010: Receive Clear Error Messages**
- View: All views
- Components: ErrorAlert
- Features: User-friendly messages, error categorization (generation/execution), guidance

**US-011: Handle Query Timeouts**
- View: Query Interface View (`/`)
- Components: ErrorAlert
- Features: Timeout error message, retry guidance

---

### Query History Stories

**US-012: View Own Query History**
- View: Query History View (`/history`)
- Components: QueryHistoryList, QueryHistoryItem, StatusBadge, Pagination
- Features: Reverse chronological list, status badges, timestamps, pagination

**US-013: Re-run Historical Query**
- View: Query History View (`/history`), Query Detail View (`/query/{id}`)
- Components: Button (Re-run)
- Features: Re-run button, new query attempt, navigation to Query Interface

---

### Schema Management Stories

**US-014: Admin Schema Refresh**
- View: Admin Schema Management View (`/admin/schema`)
- Components: SchemaSnapshotCard, RefreshButton, StatusIndicator
- Features: Refresh button, loading indicator, success/error messages, snapshot details

---

### Edge Case Stories

**US-015: Handle Empty Input**
- View: Query Interface View (`/`)
- Components: QueryForm, ErrorAlert
- Features: Submit button disabled when empty, validation error message

**US-016: Handle Large Result Sets**
- View: Query Interface View (`/`), Query Detail View (`/query/{id}`)
- Components: Pagination, ErrorAlert (truncation warning)
- Features: Pagination for 500+ rows, export truncation warning for 10K+ rows

**US-017: Handle Non-SELECT SQL**
- View: Query Interface View (`/`)
- Components: ErrorAlert
- Features: SQL validation error message, retry guidance

**US-019: Handle API Failures**
- View: All views
- Components: ErrorAlert
- Features: Service unavailable message, retry mechanism (3 attempts), user retry option

**US-020: Handle Concurrent Users**
- Mechanism: Backend connection pooling
- Features: Independent query processing, no blocking, per-user results isolation

---

### User Experience Stories

**US-021: View Query Examples**
- View: Query Interface View (`/`)
- Components: ExampleQuestions
- Features: 5-10 example questions, clickable to populate form, relevant to database

**US-022: Copy Generated SQL**
- View: Query Interface View (`/`), Query Detail View (`/query/{id}`)
- Components: SqlPreview, Button (Copy), Toast
- Features: Copy button, clipboard functionality, confirmation message

**US-023: View Execution Time**
- View: Query Interface View (`/`), Query Detail View (`/query/{id}`)
- Components: PerformanceMetrics
- Features: Execution time display, generation time display, performance indicators

---

## 7. Accessibility Requirements Summary

### WCAG Compliance Level

Target: WCAG 2.1 Level AA

### Keyboard Navigation

**Global**:
- Tab order follows logical flow
- Visible focus indicators on all interactive elements
- Skip to main content link

**View-Specific**:
- Login: Tab through username → password → login button
- Query Interface: Tab through textarea → examples → generate → (SQL preview) → execute → (results) → pagination
- History: Tab through filter → query items → expand/collapse → re-run buttons → pagination
- Admin views: Tab through action buttons → form fields

**Keyboard Shortcuts** (optional Phase 2):
- Ctrl+Enter: Submit query from textarea
- Escape: Close dropdowns/modals

---

### Screen Reader Support

**Announcements**:
- Loading states announced with aria-live="polite"
- Error messages announced with role="alert"
- Success messages announced with aria-live="polite"
- Page changes announced (history pagination)
- Status updates announced (query execution complete)

**Semantic HTML**:
- Heading hierarchy (h1 → h2 → h3)
- Landmark regions (header, main, nav, aside, footer)
- Lists (ul/ol) for navigation and history
- Tables (thead/tbody) for results
- Form labels associated with inputs

**ARIA Attributes**:
- aria-label for icon-only buttons
- aria-expanded for expandable sections
- aria-current for active navigation
- aria-disabled for disabled elements
- aria-describedby for error messages linked to fields

---

### Color and Contrast

**Requirements**:
- Text contrast ratio ≥ 4.5:1 (normal text)
- Large text contrast ratio ≥ 3:1
- Interactive element contrast ≥ 3:1

**Status Colors**:
- Success: Green (#22c55e) with checkmark icon
- Error: Red (#ef4444) with X icon
- Warning: Yellow (#f59e0b) with warning icon
- Info: Blue (#3b82f6) with info icon
- Not relying on color alone (icons + text)

---

### Focus Management

**Navigation Focus**:
- Focus moves to main heading when view changes
- Focus returns to trigger element when closing modals/dropdowns
- Focus trap in modal dialogs (if implemented)

**Skip Links**:
- "Skip to main content" link at top of page
- "Skip to results" link after SQL generation

---

### Alternative Text

**Images**:
- Logo has alt text: "SQL AI Agent"
- Status icons have alt text: "Success", "Failed", "In Progress"
- Decorative images have empty alt: alt=""

**Data Visualization**:
- Charts (if implemented) have text alternatives
- Tables used for tabular data, not layout

---

## 8. Security Considerations Summary

### Authentication Security

**Session Management**:
- HttpOnly cookies prevent XSS access
- Secure flag enforces HTTPS
- SameSite=Strict prevents CSRF
- 8-hour expiration limits exposure
- Session revocation on logout

**Password Security**:
- No client-side password storage
- No password reveal toggle (MVP)
- Generic error messages prevent username enumeration
- Rate limiting on login (5 attempts / 15 minutes)

---

### Authorization Security

**Role-Based Access**:
- Non-admin users cannot access admin routes
- Client-side routing protection + backend enforcement
- Query results filtered by user ownership
- Admin badge clearly visible

**Data Isolation**:
- Users see only their own query history
- Non-admin users cannot view other users' queries
- API enforces user_id filtering on backend

---

### Input Security

**Validation**:
- Client-side validation for immediate feedback
- Server-side validation as source of truth
- Character limits enforced (5000 chars for queries)
- Empty/whitespace-only input rejected

**Sanitization**:
- React's default XSS protection via escaping
- No use of dangerouslySetInnerHTML
- SQL preview displayed as text, not executed inline
- Form inputs sanitized before API submission

**SQL Injection Prevention**:
- Backend validates SELECT-only queries
- No direct SQL editing by users
- Preview-then-execute workflow
- Read-only database connection

---

### API Security

**Request Security**:
- HTTPS enforcement in production
- Session token in HttpOnly cookie
- CSRF protection via SameSite cookies
- Rate limiting on API endpoints

**Response Security**:
- No sensitive data in error messages
- No stack traces exposed to users
- Generic error messages for system failures
- No PII in logs or analytics

---

### Content Security

**XSS Prevention**:
- React automatically escapes content
- No dangerouslySetInnerHTML usage
- SQL preview rendered as code text
- User input not executed as HTML/JS

**Data Exposure**:
- Query results may contain sensitive data
- Users warned not to share CSV exports
- No query results cached client-side
- Session expiration clears all cached data

---

## 9. Responsive Design Strategy

### Breakpoints

**Mobile**: < 768px
**Tablet**: 768px - 1024px
**Desktop**: > 1024px

---

### Mobile Adaptations (< 768px)

**Header**:
- Hamburger menu for navigation
- User menu icon-only
- Collapsible admin dropdown

**Query Interface**:
- Full-width textarea
- Stacked example questions (vertical list)
- SQL preview with horizontal scroll
- Results table with horizontal scroll + frozen first column
- Pagination buttons full-width

**History**:
- Query items stacked vertically
- Truncated timestamps (relative only)
- Collapsed SQL preview by default
- Filter dropdown full-width

**Forms**:
- Full-width inputs
- Full-width buttons
- Larger touch targets (44x44px minimum)

---

### Tablet Adaptations (768px - 1024px)

**Header**:
- Full navigation visible
- Condensed spacing

**Query Interface**:
- Constrained textarea width (80%)
- Side-by-side example questions (2 columns)
- Results table full-width with responsive columns

**History**:
- 2-column grid for query items
- Expanded SQL preview available

---

### Desktop Adaptations (> 1024px)

**Header**:
- Full navigation with spacing
- User menu with username visible

**Query Interface**:
- Centered content (max-width 1200px)
- Side panel for examples (optional)
- Results table with optimal column widths
- Hover states on interactive elements

**History**:
- 3-column grid for query items (optional)
- Expanded SQL preview by default

---

### Touch Optimization

**Target Sizes**:
- Minimum 44x44px touch targets
- Increased padding on mobile buttons
- Larger checkboxes/radio buttons

**Gestures**:
- Swipe to dismiss toasts
- Pull-to-refresh (optional Phase 2)
- No hover-dependent interactions

---

## 10. Performance Considerations

### Loading States

**Skeleton Screens**:
- Query history loading: skeleton list items
- Results loading: skeleton table rows
- Admin metrics loading: skeleton cards

**Progressive Loading**:
- Two-stage loading indicator for SQL generation
- Execution loading with timeout indicator

---

### Code Splitting

**Route-Based**:
- Login view (separate bundle)
- Query Interface (main bundle)
- History view (lazy loaded)
- Admin views (lazy loaded, admin-only)

**Component-Based**:
- SQL preview library (lazy loaded)
- Chart library (lazy loaded, admin-only)

---

### Data Optimization

**Pagination**:
- 500 rows per page for results
- 20 queries per page for history
- Lazy load additional pages

**Caching**:
- Query form input in sessionStorage
- Authentication context in memory
- No client-side caching of results (privacy)

---

### Render Optimization

**Memoization**:
- Results table rows (React.memo)
- SQL preview (React.memo)
- Complex calculations (useMemo)

**Debouncing**:
- Not needed for MVP (no autocomplete/search-as-you-type)

**Virtual Scrolling**:
- Not needed for MVP (500 row limit sufficient)

---

## 11. Error Handling Strategy

### Error Categories

**Network Errors**:
- No internet connection
- API server unavailable
- Request timeout

**Authentication Errors**:
- Invalid credentials (401)
- Session expired (401)
- Insufficient permissions (403)

**Validation Errors**:
- Empty query input (400)
- Character limit exceeded (400)
- Invalid SQL generated (400)

**Execution Errors**:
- SQL generation failed
- Query execution failed
- Query timeout

**System Errors**:
- React component errors (ErrorBoundary)
- Unexpected API errors (500)
- LLM service unavailable (503)

---

### Error Display Patterns

**Inline Errors** (field-level):
- Form validation errors
- Input constraint violations
- Display below input field
- Red text with error icon

**Alert Errors** (view-level):
- SQL generation failures
- Query execution failures
- API errors
- Display above content
- Dismissible with action button

**Toast Errors** (system-level):
- Network errors
- Session expiration
- Rate limiting
- Display top-right or bottom-center
- Auto-dismiss after 5 seconds

**Page Errors** (full-page):
- 404 Not Found
- 403 Forbidden
- ErrorBoundary fallback
- Full-page message with navigation

---

### Error Recovery Actions

**Retry**:
- Try Again button for generation failures
- Re-submit query with modifications
- Automatic API retries (3 attempts)

**Redirect**:
- Session expiration → Login
- 403 Forbidden → Query Interface or Login
- 404 Not Found → Query Interface

**Fallback**:
- ErrorBoundary → Refresh page action
- API unavailable → Graceful degradation message

---

## 12. Future Enhancements (Post-MVP)

### Phase 2 Features

**User Experience**:
- Query modification before retry (edit SQL)
- Similar queries used display
- Table selection reasoning
- Advanced pagination (configurable page size, sorting)
- Dark mode
- Session extension warnings
- Keyboard shortcuts

**Admin Features**:
- Schema refresh UI with status indicators
- Cache age monitoring
- Cross-user query history view
- Usage analytics dashboard
- System health monitoring
- User account management interface
- Detailed query metadata tracking

**Knowledge Base**:
- Web UI for adding/editing queries
- Usage analytics for approved queries
- Dynamic embedding regeneration
- Automatic query curation
- Complex file management

**Advanced Features**:
- Scheduled schema refresh
- Query performance optimization
- Multiple database connections
- Data visualizations (charts/graphs)
- Query scheduling
- Mobile applications
- Real-time collaboration

---

This comprehensive UI architecture provides a solid foundation for implementing the SQL AI Agent MVP, with clear paths for future enhancements based on user feedback and usage patterns.
