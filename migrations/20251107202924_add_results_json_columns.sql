-- =============================================================================
-- Migration: Add columns_json and results_json to query_results_manifest
-- Date: 2025-11-07
-- Description: Add JSON columns to store query results for pagination and export
-- =============================================================================

-- Add columns_json column to store column names as JSON array
alter table query_results_manifest add column columns_json text;

-- Add results_json column to store query results as JSON array of arrays
alter table query_results_manifest add column results_json text;

-- =============================================================================
-- Migration complete
-- =============================================================================
