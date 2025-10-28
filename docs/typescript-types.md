# TypeScript Type Generation

This document explains how to generate and use TypeScript types from the database schema.

## Overview

The project includes a Python script that automatically generates TypeScript type definitions from the SQLite database schema. This ensures type safety in the frontend by keeping TypeScript types in sync with the database structure.

## Generating Types

To generate TypeScript types from the current database schema:

```bash
make generate-types
```

This will:
1. Read the database schema from [`data/app_data/app.db`](../data/app_data/app.db)
2. Generate TypeScript interfaces for all tables
3. Create utility types for common fields
4. Write the output to [`frontend/src/types/database.types.ts`](../frontend/src/types/database.types.ts)

## Prerequisites

- Database must be initialized first: `make db-init`
- Python 3 must be installed

## Generated Output

The script generates:

### Table Interfaces
Each database table gets a corresponding TypeScript interface with PascalCase naming:
- `users` → `Users`
- `query_attempts` → `QueryAttempts`
- `schema_snapshots` → `SchemaSnapshots`

### Type Mappings
SQLite types are mapped to TypeScript as follows:
- `INTEGER` → `number`
- `TEXT` → `string`
- `BLOB` → `Uint8Array`
- `DATETIME` → `string` (ISO 8601 format)

### Utility Types
Additional utility types are provided:
- `ID` - number type for primary keys
- `Timestamp` - string type for ISO 8601 timestamps
- `UserRole` - `'admin' | 'user'`
- `QueryStatus` - `'not_executed' | 'failed_generation' | 'failed_execution' | 'success' | 'timeout'`

## Usage Example

```typescript
import { Users, QueryAttempts, QueryStatus } from '../types/database.types';

// Type-safe user object
const user: Users = {
  id: 1,
  username: 'admin',
  password_hash: '$2b$12$...',
  role: 'admin',
  active: 1,
  created_at: '2025-10-26T15:52:27Z'
};

// Type-safe query attempt
const query: QueryAttempts = {
  id: 1,
  user_id: user.id,
  natural_language_query: 'Show me all users',
  generated_sql: 'SELECT * FROM users',
  status: 'success',
  created_at: '2025-10-28T12:00:00Z',
  generated_at: '2025-10-28T12:00:01Z',
  executed_at: '2025-10-28T12:00:02Z',
  generation_ms: 150,
  execution_ms: 5,
  original_attempt_id: null
};

// Type-safe status checking
const isSuccess = (status: QueryStatus): boolean => {
  return status === 'success';
};
```

## Nullable Fields

Fields that are nullable in the database are marked with `?` and include `| null` in their type:

```typescript
export interface QueryAttempts {
  id: number;                           // NOT NULL
  generated_sql?: string | null;        // nullable
  generation_ms?: number | null;        // nullable
}
```

## JSDoc Comments

The generated types include helpful JSDoc comments:
- Primary keys are marked with `/** Primary key */`
- Foreign keys are marked with `/** Foreign key reference */`
- Timestamps are marked with `/** ISO 8601 timestamp */`

## Regenerating After Schema Changes

Whenever you modify the database schema (add migrations, change tables), regenerate the types:

```bash
make db-migrate      # Apply new migrations
make generate-types  # Regenerate TypeScript types
```

## Script Details

The generation script is located at [`scripts/generate_types.py`](../scripts/generate_types.py) and:
- Connects to the SQLite database
- Reads the schema using `PRAGMA table_info()`
- Maps SQLite types to TypeScript types
- Generates properly formatted TypeScript interfaces
- Includes proper nullable handling
- Adds helpful JSDoc comments

## Troubleshooting

**Error: Database not found**
```
Error: Database not found at ./data/app_data/app.db
Please run 'make db-init' first to create the database.
```
Solution: Initialize the database first with `make db-init`

**No tables found**
```
Warning: No tables found in database
```
Solution: Ensure migrations have been applied with `make db-migrate`

## Integration with Frontend

Add the types to your frontend TypeScript configuration:

```json
{
  "compilerOptions": {
    "typeRoots": ["./src/types", "./node_modules/@types"]
  }
}
```

Import types as needed:

```typescript
import type { Users, QueryAttempts } from '@/types/database.types';
```

## Best Practices

1. **Regenerate after schema changes** - Always regenerate types when the database schema changes
2. **Use utility types** - Use `ID`, `Timestamp`, `UserRole`, `QueryStatus` for consistency
3. **Don't modify generated file** - The file is auto-generated and will be overwritten
4. **Version control** - Commit the generated types file to version control
5. **CI/CD integration** - Add type generation to your build pipeline to catch schema mismatches early

## See Also

- [Database Migrations](./migrations.md)
- [Database Schema](../migrations/20251026155227_initial_schema.sql)
- [Project Structure](../project_structure.md)