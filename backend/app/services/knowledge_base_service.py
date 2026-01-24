"""
Knowledge Base Service for loading and searching SQL examples.

Loads SQL examples from data/knowledge_base/ and provides similarity search
to find relevant examples for the LLM context using embeddings.
"""

import json
import logging
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


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
        self._embeddings_file = Path("data/knowledge_base/embeddings.json")

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
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title (first line or from filename)
        lines = content.strip().split("\n")
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
            embedding=None,  # Will be populated if embeddings are enabled
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
        if lines and not lines[0].strip().startswith(("SELECT", "--", "```")):
            # First line is the title
            title = lines[0].strip()
            # Remove markdown code block markers
            title = title.replace("```", "").strip()
            if title:
                return title

        # Convert filename to title
        # Example: "drivers_with_current_availability" -> "Drivers With Current Availability"
        title = filename_stem.replace("_", " ").title()
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
            r"--\s*Description:\s*(.+)",
            r"--\s*Question:\s*(.+)",
            r"/\*\s*Description:\s*(.+?)\*/",
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
        cleaned = re.sub(r"```sql\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"```\s*$", "", cleaned)
        cleaned = cleaned.replace("```", "")

        # Remove first line if it's a title (doesn't start with SELECT, --, etc.)
        lines = cleaned.split("\n")
        # Skip empty lines at the beginning
        while lines and not lines[0].strip():
            lines = lines[1:]
        # Remove first non-empty line if it's a title
        if lines and not lines[0].strip().upper().startswith(
            (
                "SELECT",
                "WITH",
                "INSERT",
                "UPDATE",
                "DELETE",
                "CREATE",
                "ALTER",
                "DROP",
                "--",
            )
        ):
            lines = lines[1:]

        cleaned = "\n".join(lines).strip()

        # Ensure ends with semicolon
        if not cleaned.endswith(";"):
            cleaned += ";"

        return cleaned

    def get_examples(self) -> list[KBExample]:
        """
        Get cached examples, loading from disk if not cached.

        Implements lazy loading and caching for performance.
        Also loads embeddings if available.

        Returns:
            list[KBExample]: All SQL examples
        """
        if self._examples_cache is None:
            logger.info("Examples not cached, loading from disk")
            self._examples_cache = self.load_examples()
            self.load_embeddings()  # Load embeddings after loading examples
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

        logger.info(f"Keyword search for '{keyword}' found {len(matching)} examples")

        return matching

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Cosine similarity measures the cosine of the angle between two vectors,
        ranging from -1 (opposite) to 1 (identical).

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            float: Cosine similarity score (0.0 to 1.0)

        Example:
            >>> service = KnowledgeBaseService()
            >>> similarity = service._cosine_similarity([1, 0, 0], [1, 0, 0])
            >>> similarity
            1.0
        """
        if len(vec1) != len(vec2):
            raise ValueError(
                f"Vectors must have same length: {len(vec1)} vs {len(vec2)}"
            )

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)

        return similarity

    async def find_similar_examples(
        self,
        question: str,
        question_embedding: list[float] | None = None,
        top_k: int = 3,
    ) -> tuple[list[KBExample], float]:
        """
        Find most similar examples for a given question using embeddings.

        If embeddings are available, uses cosine similarity to find the most
        relevant examples. If the highest similarity is above the threshold,
        returns that example as the primary match.

        Args:
            question: User's natural language question
            question_embedding: Pre-computed embedding for the question (optional)
            top_k: Number of examples to return

        Returns:
            tuple: (list of similar examples, highest similarity score)
                   Examples are sorted by similarity (most similar first)

        Example:
            >>> service = KnowledgeBaseService()
            >>> examples, max_sim = await service.find_similar_examples(
            ...     "Show current driver status",
            ...     question_embedding=[0.1, 0.2, ...]
            ... )
            >>> if max_sim > 0.85:
            ...     print(f"Exact match found: {examples[0].title}")
        """
        examples = self.get_examples()

        # Check if embeddings are available
        embeddings_available = all(ex.embedding is not None for ex in examples)

        if not embeddings_available or question_embedding is None:
            # Fallback: Return all examples without similarity ranking
            logger.info(f"Embeddings not available, returning first {top_k} examples")
            return examples[:top_k], 0.0

        # Calculate similarity scores for all examples
        similarities: list[tuple[KBExample, float]] = []

        for example in examples:
            if example.embedding is None:
                continue

            similarity = self._cosine_similarity(question_embedding, example.embedding)
            similarities.append((example, similarity))

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Get top K examples
        top_examples = [ex for ex, _ in similarities[:top_k]]
        max_similarity = similarities[0][1] if similarities else 0.0

        logger.info(
            f"Found {len(top_examples)} similar examples. "
            f"Highest similarity: {max_similarity:.3f}"
        )

        # Log top matches for debugging
        for i, (example, sim) in enumerate(similarities[:top_k]):
            logger.debug(f"  {i+1}. {example.title}: {sim:.3f}")

        return top_examples, max_similarity

    def save_embeddings(self) -> None:
        """
        Save embeddings to disk as JSON file.

        Persists embeddings so they don't need to be regenerated on restart.
        """
        examples = self.get_examples()

        embeddings_data = []
        for example in examples:
            embeddings_data.append(
                {"filename": example.filename, "embedding": example.embedding}
            )

        with open(self._embeddings_file, "w") as f:
            json.dump(embeddings_data, f)

        logger.info(
            f"Saved embeddings for {len(embeddings_data)} examples to {self._embeddings_file}"
        )

    def load_embeddings(self) -> None:
        """
        Load embeddings from disk and attach to examples.

        If embeddings file doesn't exist, silently skips loading.
        """
        if not self._embeddings_file.exists():
            logger.info("No embeddings file found, skipping load")
            return

        try:
            with open(self._embeddings_file, "r") as f:
                embeddings_data = json.load(f)

            examples = self.get_examples()

            # Create a map of filename to embedding
            embedding_map = {
                item["filename"]: item["embedding"] for item in embeddings_data
            }

            # Attach embeddings to examples
            loaded_count = 0
            for example in examples:
                if example.filename in embedding_map:
                    example.embedding = embedding_map[example.filename]
                    loaded_count += 1

            logger.info(
                f"Loaded embeddings for {loaded_count}/{len(examples)} examples"
            )

        except Exception as e:
            logger.warning(f"Failed to load embeddings: {e}")

    async def generate_embeddings(self, llm_service) -> dict[str, Any]:
        """
        Generate embeddings for all examples using OpenAI.

        This should be called once initially or when new examples are added.

        Args:
            llm_service: LLMService instance for generating embeddings

        Returns:
            dict: Statistics about embedding generation

        Example:
            >>> from backend.app.services.llm_service import LLMService
            >>> kb_service = KnowledgeBaseService()
            >>> llm_service = LLMService()
            >>> stats = await kb_service.generate_embeddings(llm_service)
            >>> print(f"Generated {stats['embeddings_generated']} embeddings")
        """
        examples = self.get_examples()

        embeddings_generated = 0
        embeddings_skipped = 0

        logger.info(f"Generating embeddings for {len(examples)} examples")

        for example in examples:
            if example.embedding is not None:
                logger.debug(f"Skipping {example.filename} (already has embedding)")
                embeddings_skipped += 1
                continue

            try:
                # Generate embedding from example's SQL + title + description
                text_to_embed = (
                    f"{example.title}\n{example.description or ''}\n{example.sql}"
                )

                embedding = await llm_service.generate_embedding(text_to_embed)
                example.embedding = embedding
                embeddings_generated += 1

                logger.info(f"Generated embedding for {example.filename}")

            except Exception as e:
                logger.error(
                    f"Failed to generate embedding for {example.filename}: {e}"
                )
                continue

        # Save embeddings to disk
        self.save_embeddings()

        stats = {
            "total_examples": len(examples),
            "embeddings_generated": embeddings_generated,
            "embeddings_skipped": embeddings_skipped,
            "embeddings_available": sum(
                1 for ex in examples if ex.embedding is not None
            ),
        }

        logger.info(f"Embedding generation complete: {stats}")

        return stats

    def refresh_examples(self) -> list[KBExample]:
        """
        Reload examples from disk, clearing cache.

        Used by admin endpoints to refresh KB without restart.

        Returns:
            list[KBExample]: Newly loaded examples
        """
        logger.info("Refreshing knowledge base cache (admin request)")
        self._examples_cache = None
        examples = self.load_examples()
        self.load_embeddings()  # Load embeddings after loading examples
        return examples

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
            "examples_with_descriptions": sum(1 for ex in examples if ex.description),
            "kb_directory": str(self._kb_directory),
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
