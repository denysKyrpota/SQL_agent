"""
Knowledge Base Service for loading and searching SQL examples.

Loads SQL examples from data/knowledge_base/ and provides similarity search
to find relevant examples for the LLM context.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KBExample:
    """
    Knowledge base SQL example.

    Attributes:
        filename: Original filename (e.g., "drivers_with_current_availability.sql")
        title: Human-readable title extracted from file
        description: Description of what the query does
        sql: The actual SQL query
        embedding: Vector embedding for similarity search (optional)
    """
    filename: str
    title: str
    description: str | None
    sql: str
    embedding: list[float] | None = None


class KnowledgeBaseService:
    """
    Service for managing SQL query examples from the knowledge base.

    Loads .sql files from data/knowledge_base/ directory and provides
    search capabilities to find relevant examples for SQL generation.
    """

    def __init__(self):
        """Initialize the knowledge base service with empty cache."""
        self._examples_cache: list[KBExample] | None = None
        self._kb_directory = Path("data/knowledge_base")

    def load_examples(self) -> list[KBExample]:
        """
        Load all SQL examples from knowledge base directory.

        Reads all .sql files from data/knowledge_base/ and parses them
        into structured examples.

        Returns:
            list[KBExample]: List of loaded SQL examples

        Raises:
            FileNotFoundError: If knowledge base directory doesn't exist
        """
        if not self._kb_directory.exists():
            error_msg = f"Knowledge base directory not found: {self._kb_directory}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"Loading SQL examples from {self._kb_directory}")

        examples = []
        sql_files = sorted(self._kb_directory.glob("*.sql"))

        for sql_file in sql_files:
            try:
                example = self._load_example_file(sql_file)
                examples.append(example)
                logger.debug(f"Loaded example: {example.title} from {sql_file.name}")
            except Exception as e:
                logger.warning(f"Failed to load {sql_file.name}: {e}")
                continue

        logger.info(f"Loaded {len(examples)} SQL examples from knowledge base")

        return examples

    def _load_example_file(self, file_path: Path) -> KBExample:
        """
        Load and parse a single SQL example file.

        File format expected:
        ```
        Title of the query
        ```sql
        SELECT ...
        ```

        Or:
        ```
        -- Description: What this query does
        SELECT ...
        ```

        Args:
            file_path: Path to .sql file

        Returns:
            KBExample: Parsed example
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title (first line or from filename)
        lines = content.strip().split('\n')
        title = self._extract_title(lines, file_path.stem)

        # Extract description (optional)
        description = self._extract_description(content)

        # Extract SQL (remove markdown, comments, etc.)
        sql = self._extract_sql(content)

        return KBExample(
            filename=file_path.name,
            title=title,
            description=description,
            sql=sql,
            embedding=None  # Will be populated if embeddings are enabled
        )

    def _extract_title(self, lines: list[str], filename_stem: str) -> str:
        """
        Extract title from first line or convert filename to title.

        Args:
            lines: File content lines
            filename_stem: Filename without extension

        Returns:
            str: Human-readable title
        """
        if lines and not lines[0].strip().startswith(('SELECT', '--', '```')):
            # First line is the title
            title = lines[0].strip()
            # Remove markdown code block markers
            title = title.replace('```', '').strip()
            if title:
                return title

        # Convert filename to title
        # Example: "drivers_with_current_availability" -> "Drivers With Current Availability"
        title = filename_stem.replace('_', ' ').title()
        return title

    def _extract_description(self, content: str) -> str | None:
        """
        Extract description from SQL comments.

        Looks for patterns like:
        -- Description: ...
        -- Question: ...

        Args:
            content: Full file content

        Returns:
            str | None: Description if found
        """
        # Look for description patterns
        patterns = [
            r'--\s*Description:\s*(.+)',
            r'--\s*Question:\s*(.+)',
            r'/\*\s*Description:\s*(.+?)\*/',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_sql(self, content: str) -> str:
        """
        Extract SQL query from file content.

        Removes:
        - Markdown code blocks (```sql)
        - Title lines
        - Leading/trailing whitespace

        Args:
            content: Full file content

        Returns:
            str: Cleaned SQL query
        """
        cleaned = content

        # Remove markdown code blocks
        cleaned = re.sub(r'```sql\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        cleaned = cleaned.replace('```', '')

        # Remove first line if it's a title (doesn't start with SELECT, --, etc.)
        lines = cleaned.split('\n')
        if lines and not lines[0].strip().upper().startswith(('SELECT', 'WITH', '--')):
            lines = lines[1:]

        cleaned = '\n'.join(lines).strip()

        # Ensure ends with semicolon
        if not cleaned.endswith(';'):
            cleaned += ';'

        return cleaned

    def get_examples(self) -> list[KBExample]:
        """
        Get cached examples, loading from disk if not cached.

        Implements lazy loading and caching for performance.

        Returns:
            list[KBExample]: All SQL examples
        """
        if self._examples_cache is None:
            logger.info("Examples not cached, loading from disk")
            self._examples_cache = self.load_examples()
        else:
            logger.debug("Returning cached examples")

        return self._examples_cache

    def get_all_examples_text(self) -> list[str]:
        """
        Get all examples as SQL text (for simple LLM context).

        For MVP, we can send all examples to the LLM without embeddings.
        With only 7 examples, this is feasible.

        Returns:
            list[str]: List of SQL queries
        """
        examples = self.get_examples()
        return [example.sql for example in examples]

    def find_examples_by_keyword(self, keyword: str) -> list[KBExample]:
        """
        Find examples containing a keyword in title, description, or SQL.

        Simple keyword search without embeddings.

        Args:
            keyword: Search term (case-insensitive)

        Returns:
            list[KBExample]: Matching examples
        """
        examples = self.get_examples()
        keyword_lower = keyword.lower()

        matching = []
        for example in examples:
            # Check title
            if keyword_lower in example.title.lower():
                matching.append(example)
                continue

            # Check description
            if example.description and keyword_lower in example.description.lower():
                matching.append(example)
                continue

            # Check SQL
            if keyword_lower in example.sql.lower():
                matching.append(example)

        logger.info(
            f"Keyword search for '{keyword}' found {len(matching)} examples"
        )

        return matching

    async def find_similar_examples(
        self,
        question: str,
        top_k: int = 3
    ) -> list[KBExample]:
        """
        Find most similar examples for a given question.

        MVP IMPLEMENTATION: Returns all examples (no embeddings yet).
        With only 7 examples, we can send all of them to the LLM.

        Future enhancement: Use embeddings + cosine similarity for
        smarter example selection when KB grows larger.

        Args:
            question: User's natural language question
            top_k: Number of examples to return

        Returns:
            list[KBExample]: Most similar examples (or all if < top_k)
        """
        examples = self.get_examples()

        # MVP: Return all examples (only 7, so LLM can handle them all)
        logger.info(
            f"Returning all {len(examples)} examples (embeddings not implemented)"
        )

        # If we have more examples than requested, return the first top_k
        if len(examples) > top_k:
            return examples[:top_k]

        return examples

    def refresh_examples(self) -> list[KBExample]:
        """
        Reload examples from disk, clearing cache.

        Used by admin endpoints to refresh KB without restart.

        Returns:
            list[KBExample]: Newly loaded examples
        """
        logger.info("Refreshing knowledge base cache (admin request)")
        self._examples_cache = None
        return self.load_examples()

    def get_example_by_filename(self, filename: str) -> KBExample | None:
        """
        Get a specific example by filename.

        Args:
            filename: Filename (e.g., "drivers_with_current_availability.sql")

        Returns:
            KBExample | None: Example if found
        """
        examples = self.get_examples()
        for example in examples:
            if example.filename == filename:
                return example
        return None

    def get_stats(self) -> dict[str, Any]:
        """
        Get knowledge base statistics.

        Useful for admin dashboards and monitoring.

        Returns:
            dict: Statistics about the knowledge base
        """
        examples = self.get_examples()

        total_sql_length = sum(len(ex.sql) for ex in examples)
        avg_sql_length = total_sql_length // len(examples) if examples else 0

        return {
            "total_examples": len(examples),
            "total_sql_length": total_sql_length,
            "average_sql_length": avg_sql_length,
            "examples_with_descriptions": sum(
                1 for ex in examples if ex.description
            ),
            "kb_directory": str(self._kb_directory)
        }


# Future enhancement: Embedding-based similarity search
#
# async def generate_embeddings(self, llm_service):
#     """Generate embeddings for all examples using OpenAI."""
#     examples = self.get_examples()
#
#     for example in examples:
#         if example.embedding is None:
#             # Generate embedding using OpenAI embeddings API
#             embedding = await llm_service.generate_embedding(example.sql)
#             example.embedding = embedding
#
# def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
#     """Calculate cosine similarity between two vectors."""
#     import numpy as np
#     return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
