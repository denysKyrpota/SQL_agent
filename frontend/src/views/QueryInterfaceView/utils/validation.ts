/**
 * Validation utilities for Query Interface
 */

/**
 * Validates a natural language query
 * @param query - The query string to validate
 * @returns Error message if invalid, null if valid
 */
export const validateQuery = (query: string): string | null => {
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

/**
 * Checks if query is valid for submission
 * @param query - The query string to check
 * @returns true if valid, false otherwise
 */
export const isQueryValid = (query: string): boolean => {
  return validateQuery(query) === null;
};
