# Data Directory Structure - Example

This folder provides the structure and format for the `data/` directory. The actual `data/` folder is excluded from version control as it contains sensitive business and database information.

## Setup Instructions

1. **Copy this structure** to create your own `data/` folder:
   ```bash
   cp -r data_example data
   ```

2. **Generate your database schema**:
   ```bash
   # The application will automatically cache your PostgreSQL schema
   # when you first connect. Schema files will be saved in data/schema/
   ```

3. **Create knowledge base examples**:
   - Add SQL query examples to `data/knowledge_base/`
   - Each file should contain one SQL query with optional title/description
   - See examples in `data_example/knowledge_base/` for format

4. **Generate embeddings**:
   ```bash
   # Use the admin API to generate embeddings for your knowledge base
   curl -X POST http://localhost:8000/api/admin/knowledge-base/embeddings/generate \
     -H "Authorization: Bearer <admin_token>"
   ```

## Directory Structure

```
data/
├── README.md                      # This file (optional in actual data/)
├── knowledge_base/                # SQL example queries for RAG
│   ├── example_query_1.sql        # Example SQL queries
│   ├── example_query_2.sql
│   └── embeddings.json            # Generated embeddings (auto-created)
│
├── schema/                        # PostgreSQL schema cache (auto-generated)
│   └── *.json                     # Schema snapshot files
│
├── app_data/                      # Application SQLite database
│   └── app.db                     # Created automatically on first run
│
└── exports/                       # CSV export storage
    └── .gitkeep
```

## Knowledge Base File Format

Each `.sql` file in `knowledge_base/` should follow this format:

```sql
-- Title: Brief description of what this query does
-- Description: More detailed explanation (optional)

SELECT column1, column2
FROM table_name
WHERE condition = 'value';
```

The title and description are optional but recommended for better RAG matching.

## Schema Files

Schema files are automatically generated when the application connects to your PostgreSQL database. You don't need to create these manually.

## Important Notes

- **Never commit the actual `data/` folder** - it's in `.gitignore`
- The `data/` folder contains sensitive business information
- Each deployment/environment should have its own `data/` folder
- The application will create missing directories automatically
