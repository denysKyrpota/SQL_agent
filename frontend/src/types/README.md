# Frontend Types (TypeScript)

This directory contains all TypeScript type definitions for the React frontend application.

## Structure

- **`index.ts`** - Central export point for all types
- **`common.ts`** - Shared types, enums, and base interfaces
- **`models.ts`** - Domain model types (User, QueryAttempt, etc.)
- **`api.ts`** - API request/response types
- **`utils.ts`** - Type guards and utility functions
- **`database.types.ts`** - Auto-generated from database schema

## Usage

### Importing Types

Always import from the package level:

```typescript
import type {
  LoginRequest,
  LoginResponse,
  QueryAttemptResponse,
  User,
} from "@/types";
```

### Using in Components

```typescript
import { useState } from "react";
import type { User, QueryAttempt } from "@/types";

function UserProfile({ user }: { user: User }) {
  const [queries, setQueries] = useState<QueryAttempt[]>([]);

  // TypeScript ensures type safety
  return (
    <div>
      <h1>{user.username}</h1>
      <p>Role: {user.role}</p>
    </div>
  );
}
```

### Using in API Calls

```typescript
import type { LoginRequest, LoginResponse } from "@/types";

async function login(request: LoginRequest): Promise<LoginResponse> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error("Login failed");
  }

  return response.json() as Promise<LoginResponse>;
}
```

### Using Type Guards

```typescript
import { isQueryStatus, isAPIError } from "@/types/utils";

// Runtime validation
function processStatus(value: unknown) {
  if (isQueryStatus(value)) {
    // TypeScript knows value is QueryStatus here
    console.log(`Status: ${value}`);
  }
}

// Error handling
try {
  await apiCall();
} catch (error) {
  if (isAPIError(error)) {
    console.error(error.detail, error.errorCode);
  }
}
```

## Type Categories

### Common Types (`common.ts`)

Shared across the application:

- `QueryStatus` - Union type for query states
- `UserRole` - Union type for user roles
- `ISO8601Timestamp` - Type alias for timestamp strings
- `PaginationMetadata` - Pagination information
- `ErrorResponse` - Standard error format

### Domain Models (`models.ts`)

Core business entities:

- `User` - User account information
- `SessionInfo` - Session details
- `QueryAttempt` - Natural language query and SQL
- `QueryAttemptDetail` - Extended with execution info
- `QueryResults` - Query execution results
- `MetricRow` - Usage metrics data

### API Types (`api.ts`)

Request/response structures for all endpoints:

**Auth:**
- `LoginRequest`, `LoginResponse`
- `SessionResponse`, `LogoutResponse`

**Queries:**
- `CreateQueryRequest`, `QueryAttemptResponse`
- `ExecuteQueryResponse`, `QueryResultsResponse`
- `QueryListResponse`, `RerunQueryResponse`

**Admin:**
- `RefreshSchemaResponse`, `ReloadKBResponse`
- `MetricsResponse`, `MetricsParams`

**System:**
- `HealthCheckResponse`

### Utility Functions (`utils.ts`)

Type guards and helpers:

- `isQueryStatus()` - Type guard for QueryStatus
- `isUserRole()` - Type guard for UserRole
- `parseISO8601()` - Parse ISO timestamp to Date
- `formatDuration()` - Format milliseconds to readable string
- `getRelativeTime()` - Get "2 minutes ago" style strings
- `getStatusLabel()` - User-friendly status labels
- `formatRate()` - Format percentages

## TypeScript Features

### Union Types

Used extensively for enums:

```typescript
export type QueryStatus =
  | "not_executed"
  | "failed_generation"
  | "failed_execution"
  | "success"
  | "timeout";
```

### Interface Extension

For creating specialized types:

```typescript
export interface QueryAttemptDetail extends QueryAttempt {
  executed_at: ISO8601Timestamp | null;
  execution_ms: number | null;
  original_attempt_id: number | null;
}
```

### Generic Types

For reusable patterns:

```typescript
export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMetadata;
}

// Usage
type UserList = PaginatedResponse<User>;
```

### Type Aliases

For clarity and reusability:

```typescript
export type ISO8601Timestamp = string;
export type UserRole = "admin" | "user";
```

### Null vs Undefined

Convention: Use `null` for API responses, `undefined` for optional properties:

```typescript
interface QueryAttempt {
  executed_at: ISO8601Timestamp | null;  // Explicitly null in API
  error_message?: string | null;         // Optional property
}
```

## Type Guards

Type guards enable runtime type checking:

```typescript
export function isQueryStatus(value: unknown): value is QueryStatus {
  return (
    typeof value === "string" &&
    ["not_executed", "failed_generation", /* ... */].includes(value)
  );
}

// Usage
const status: unknown = fetchedData.status;
if (isQueryStatus(status)) {
  // TypeScript knows status is QueryStatus now
  switch (status) {
    case "success":
      // Handle success
      break;
    // ...
  }
}
```

## Working with Dates

All dates come from the API as ISO 8601 strings:

```typescript
import { parseISO8601, getRelativeTime } from "@/types/utils";

interface QueryAttempt {
  created_at: ISO8601Timestamp;  // "2025-10-28T12:00:00Z"
}

// Convert to Date object
const date = parseISO8601(query.created_at);

// Get relative time
const timeAgo = getRelativeTime(query.created_at);  // "2 hours ago"

// Format for display
if (date) {
  const formatted = date.toLocaleDateString();
}
```

## Error Handling

Use the `APIError` class for typed error handling:

```typescript
import { APIError, isAPIError } from "@/types";

async function makeRequest() {
  try {
    const response = await fetch("/api/endpoint");
    if (!response.ok) {
      const error = await response.json();
      throw new APIError(
        response.status,
        error.detail,
        error.error_code
      );
    }
    return response.json();
  } catch (error) {
    if (isAPIError(error)) {
      // Handle API errors specifically
      console.error(`API Error (${error.status}): ${error.detail}`);
      if (error.errorCode) {
        console.error(`Code: ${error.errorCode}`);
      }
    } else {
      // Handle other errors
      console.error("Unexpected error:", error);
    }
    throw error;
  }
}
```

## Best Practices

### 1. Use `type` for Unions and Aliases

```typescript
// Good
export type QueryStatus = "success" | "failed";

// Less ideal for unions
export interface QueryStatus { ... }
```

### 2. Use `interface` for Object Shapes

```typescript
// Good
export interface User {
  id: number;
  username: string;
}

// Less ideal for objects
export type User = { ... };
```

### 3. Add JSDoc Comments

```typescript
/**
 * User information (excludes sensitive data like password).
 */
export interface User {
  /** Unique user identifier */
  id: number;
  /** Username for display and login */
  username: string;
}
```

### 4. Use Readonly for Immutable Data

```typescript
export interface User {
  readonly id: number;  // ID should never change
  username: string;     // Username can be updated
}
```

### 5. Derive Types Instead of Duplicating

```typescript
// Base type
export interface QueryAttempt {
  id: number;
  status: QueryStatus;
  created_at: ISO8601Timestamp;
}

// Derived type
export type SimplifiedQueryAttempt = Pick<
  QueryAttempt,
  "id" | "status" | "created_at"
>;
```

### 6. Use Type Guards for Runtime Safety

```typescript
// Instead of type assertion
const status = data.status as QueryStatus;  // Unsafe!

// Use type guard
if (isQueryStatus(data.status)) {
  const status = data.status;  // Safe!
}
```

### 7. Avoid `any` - Use `unknown` Instead

```typescript
// Bad
function process(data: any) { ... }

// Good
function process(data: unknown) {
  if (typeof data === "string") {
    // TypeScript enforces checking
  }
}
```

## Utility Type Examples

### Pick - Select Specific Properties

```typescript
type UserSummary = Pick<User, "id" | "username">;
// { id: number; username: string; }
```

### Omit - Exclude Properties

```typescript
type UserWithoutRole = Omit<User, "role">;
// { id: number; username: string; active: boolean; }
```

### Partial - Make All Properties Optional

```typescript
type PartialUser = Partial<User>;
// { id?: number; username?: string; role?: UserRole; active?: boolean; }
```

### Required - Make All Properties Required

```typescript
type RequiredQueryAttempt = Required<QueryAttempt>;
// All properties are now required (no | null)
```

### Record - Key-Value Mapping

```typescript
type StatusColors = Record<QueryStatus, string>;
// { not_executed: string; failed_generation: string; ... }
```

## Testing Types

### Type-Only Tests

```typescript
import { expectType, expectError } from "tsd";
import type { User, QueryStatus } from "@/types";

// Type checks at compile time
expectType<QueryStatus>("success");
expectError<QueryStatus>("invalid");

// Check structure
const user: User = {
  id: 1,
  username: "test",
  role: "admin",
  active: true,
};
expectType<User>(user);
```

### Runtime Validation Tests

```typescript
import { describe, it, expect } from "vitest";
import { isQueryStatus, isUserRole } from "@/types/utils";

describe("Type Guards", () => {
  it("validates QueryStatus", () => {
    expect(isQueryStatus("success")).toBe(true);
    expect(isQueryStatus("invalid")).toBe(false);
    expect(isQueryStatus(null)).toBe(false);
  });

  it("validates UserRole", () => {
    expect(isUserRole("admin")).toBe(true);
    expect(isUserRole("user")).toBe(true);
    expect(isUserRole("superuser")).toBe(false);
  });
});
```

## Auto-Generated Types

The `database.types.ts` file is auto-generated from the SQLite schema:

```bash
# Regenerate database types
make generate-types
```

These types mirror the database structure directly and should not be manually edited.

## Keeping Types in Sync

1. **Source of Truth**: API Plan (`.ai/api-plan.md`)
2. **Update Flow**:
   - API plan updated
   - Backend Pydantic models updated
   - Frontend TypeScript types updated
   - Integration tests verify sync

3. **Validation**:
   ```bash
   # Type check TypeScript
   npm run type-check

   # Run tests
   npm test
   ```

## Common Issues

### Issue: Type mismatch at runtime

**Cause**: API response doesn't match type definition
**Solution**: Use type guards for runtime validation

```typescript
const data = await response.json();
if (isQueryStatus(data.status)) {
  // Safe to use
}
```

### Issue: "Type 'null' is not assignable"

**Cause**: Strict null checks enabled (good!)
**Solution**: Handle null explicitly

```typescript
// Bad
const date = parseISO8601(query.created_at);
console.log(date.toISOString());  // Error if null

// Good
const date = parseISO8601(query.created_at);
if (date) {
  console.log(date.toISOString());
}
```

### Issue: "Property does not exist on type 'unknown'"

**Cause**: TypeScript protecting you from unsafe access
**Solution**: Narrow the type first

```typescript
function process(data: unknown) {
  // Bad
  console.log(data.field);  // Error

  // Good
  if (typeof data === "object" && data !== null && "field" in data) {
    console.log((data as { field: string }).field);
  }
}
```

## Related Documentation

- [API Plan](../../../../.ai/api-plan.md) - Full API specification
- [DTOs and Types](../../../../docs/dtos-and-types.md) - Cross-platform guide
- [Backend Schemas](../../../../backend/app/schemas/) - Python Pydantic models
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/) - Official docs

## Examples

See the [examples directory](./examples/) for complete usage examples (if created).

For component examples, check the main application code in `frontend/src/`.
