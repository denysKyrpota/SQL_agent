# RAG Knowledge Base: OpenAI Embeddings Implementation Plan

**Created**: 2025-11-13
**Status**: Planning
**Target**: Production-ready semantic search for 40+ SQL examples

---

## 📋 Executive Summary

Upgrade the knowledge base from naive "return all examples" to intelligent semantic search using OpenAI embeddings. This will dramatically improve SQL generation quality by providing the LLM with the most relevant examples for each query.

**Key Metrics**:
- Current: Returns all 7 examples (no intelligence)
- Target: Return top 3 most semantically similar examples
- Knowledge Base Growth: 7 → 40+ examples
- Cost: ~$0.00001 per query (negligible)
- Expected Quality Improvement: 40-60% better SQL generation accuracy

---

## 🏗️ Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Knowledge Base Service                    │
├─────────────────────────────────────────────────────────────┤
│  1. Example Loader (existing)                               │
│  2. Embedding Generator (NEW)                               │
│  3. Embeddings Cache (NEW)                                  │
│  4. Similarity Search (NEW)                                 │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ SQL Files    │    │ OpenAI API   │    │ Cache File   │
│ (.sql)       │    │ (embeddings) │    │ (.pkl/.json) │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Data Flow

```
Startup:
1. Load examples from data/knowledge_base/*.sql
2. Check if embeddings cache exists
3. If cache exists → load embeddings
4. If cache missing → generate embeddings via OpenAI → save cache

Query Time:
1. User submits question
2. Generate embedding for question (OpenAI API call)
3. Compute cosine similarity with all example embeddings
4. Return top-3 most similar examples
5. Pass to LLM for SQL generation
```

---

## 📁 File Structure

```
backend/app/services/
  ├── knowledge_base_service.py        # Main service (MODIFY)
  └── embedding_service.py              # New: Embedding utilities

data/
  ├── knowledge_base/                   # Existing SQL examples
  │   ├── example1.sql
  │   ├── example2.sql
  │   └── ... (40+ files)
  └── embeddings_cache.pkl              # New: Cached embeddings

backend/app/api/
  └── admin.py                          # Add endpoint: POST /api/admin/refresh-embeddings

tests/services/
  ├── test_knowledge_base_service.py    # Update tests
  └── test_embedding_service.py         # New: Embedding tests
```

---

## 🔧 Implementation Plan

### Phase 1: Core Embedding Infrastructure (4 hours)

#### 1.1 Create EmbeddingService (NEW FILE)
**File**: `backend/app/services/embedding_service.py`

```python
"""
Embedding Service for generating and managing OpenAI embeddings.
"""

import logging
from typing import List
import numpy as np
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI API.

    Uses text-embedding-3-small model:
    - Cost: $0.00002 per 1K tokens
    - Dimensions: 1536
    - Speed: ~100ms per request
    """

    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client
        self.model = "text-embedding-3-small"
        self.dimensions = 1536

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text (title + description + SQL)

        Returns:
            List of 1536 floats representing the embedding

        Raises:
            OpenAIError: If API call fails
        """
        try:
            logger.debug(f"Generating embedding for text ({len(text)} chars)")

            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding: {len(embedding)} dimensions")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        OpenAI allows up to 2048 texts per batch, but we use smaller
        batches to avoid timeout issues.

        Args:
            texts: List of input texts
            batch_size: Number of texts per batch

        Returns:
            List of embeddings (same order as input)
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing embedding batch {i//batch_size + 1}")

            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
                encoding_format="float"
            )

            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

        return embeddings

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score between -1 and 1 (1 = identical)
        """
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
```

**Testing**:
```python
# tests/services/test_embedding_service.py
async def test_generate_embedding(mock_openai_client):
    service = EmbeddingService(mock_openai_client)
    embedding = await service.generate_embedding("SELECT * FROM users")

    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)

async def test_cosine_similarity():
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    similarity = EmbeddingService.cosine_similarity(vec1, vec2)
    assert similarity == 1.0  # Identical vectors
```

---

#### 1.2 Update KBExample Dataclass
**File**: `backend/app/services/knowledge_base_service.py` (lines 17-33)

```python
@dataclass
class KBExample:
    """
    Knowledge base SQL example with optional embedding.

    Attributes:
        filename: Original filename
        title: Human-readable title
        description: Description of what the query does
        sql: The actual SQL query
        embedding: 1536-dim vector from OpenAI (None until generated)
        embedding_generated_at: Timestamp when embedding was created
    """
    filename: str
    title: str
    description: str | None
    sql: str
    embedding: list[float] | None = None
    embedding_generated_at: str | None = None  # ISO 8601 timestamp

    def get_searchable_text(self) -> str:
        """
        Get combined text for embedding generation.

        Combines title, description, and SQL into single text
        for semantic search.
        """
        parts = [self.title]
        if self.description:
            parts.append(self.description)
        parts.append(self.sql)

        return "\n".join(parts)
```

---

### Phase 2: Embeddings Cache (3 hours)

#### 2.1 Add Cache Management Methods
**File**: `backend/app/services/knowledge_base_service.py`

```python
import pickle
from pathlib import Path
from datetime import datetime

class KnowledgeBaseService:
    def __init__(self, embedding_service: EmbeddingService):
        self._examples_cache: list[KBExample] | None = None
        self._kb_directory = Path("data/knowledge_base")
        self._embeddings_cache_file = Path("data/embeddings_cache.pkl")
        self.embedding_service = embedding_service

    def _load_embeddings_from_cache(self) -> bool:
        """
        Load pre-computed embeddings from cache file.

        Returns:
            True if cache loaded successfully, False otherwise
        """
        if not self._embeddings_cache_file.exists():
            logger.info("Embeddings cache file not found")
            return False

        try:
            logger.info(f"Loading embeddings from {self._embeddings_cache_file}")

            with open(self._embeddings_cache_file, 'rb') as f:
                cached_data = pickle.load(f)

            # Validate cache structure
            if not isinstance(cached_data, dict):
                logger.warning("Invalid cache format")
                return False

            # Map embeddings to examples by filename
            examples = self.get_examples()
            loaded_count = 0

            for example in examples:
                if example.filename in cached_data:
                    cache_entry = cached_data[example.filename]
                    example.embedding = cache_entry['embedding']
                    example.embedding_generated_at = cache_entry['generated_at']
                    loaded_count += 1

            logger.info(f"Loaded embeddings for {loaded_count}/{len(examples)} examples")

            return loaded_count > 0

        except Exception as e:
            logger.error(f"Failed to load embeddings cache: {e}")
            return False

    def _save_embeddings_to_cache(self) -> None:
        """
        Save all embeddings to cache file.

        Saves as pickle file with structure:
        {
            "example1.sql": {
                "embedding": [1536 floats],
                "generated_at": "2025-11-13T10:30:00Z"
            },
            ...
        }
        """
        examples = self.get_examples()

        cache_data = {}
        for example in examples:
            if example.embedding is not None:
                cache_data[example.filename] = {
                    'embedding': example.embedding,
                    'generated_at': example.embedding_generated_at
                }

        # Ensure directory exists
        self._embeddings_cache_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving {len(cache_data)} embeddings to cache")

        with open(self._embeddings_cache_file, 'wb') as f:
            pickle.dump(cache_data, f)

        logger.info(f"Embeddings cache saved to {self._embeddings_cache_file}")
```

---

### Phase 3: Embedding Generation (3 hours)

#### 3.1 Add Initialization Method
**File**: `backend/app/services/knowledge_base_service.py`

```python
async def initialize_embeddings(self, force_regenerate: bool = False) -> dict:
    """
    Initialize embeddings for all examples.

    Workflow:
    1. Try to load from cache (unless force_regenerate=True)
    2. If cache missing or incomplete, generate via OpenAI
    3. Save to cache

    Args:
        force_regenerate: If True, ignore cache and regenerate all

    Returns:
        dict with statistics:
        {
            "total_examples": 40,
            "cached": 35,
            "generated": 5,
            "cost_usd": 0.0001
        }
    """
    examples = self.get_examples()
    logger.info(f"Initializing embeddings for {len(examples)} examples")

    stats = {
        "total_examples": len(examples),
        "cached": 0,
        "generated": 0,
        "cost_usd": 0.0
    }

    # Step 1: Try to load from cache
    if not force_regenerate:
        cache_loaded = self._load_embeddings_from_cache()
        if cache_loaded:
            stats["cached"] = sum(1 for ex in examples if ex.embedding is not None)

    # Step 2: Generate missing embeddings
    examples_needing_embeddings = [
        ex for ex in examples if ex.embedding is None
    ]

    if examples_needing_embeddings:
        logger.info(f"Generating embeddings for {len(examples_needing_embeddings)} examples")

        # Prepare texts
        texts = [ex.get_searchable_text() for ex in examples_needing_embeddings]

        # Generate embeddings (batch API call)
        embeddings = await self.embedding_service.generate_batch_embeddings(texts)

        # Assign embeddings
        timestamp = datetime.utcnow().isoformat() + "Z"
        for example, embedding in zip(examples_needing_embeddings, embeddings):
            example.embedding = embedding
            example.embedding_generated_at = timestamp

        stats["generated"] = len(examples_needing_embeddings)

        # Estimate cost: $0.00002 per 1K tokens, assume ~500 tokens per example
        tokens_used = len(examples_needing_embeddings) * 500
        stats["cost_usd"] = (tokens_used / 1000) * 0.00002

        # Step 3: Save to cache
        self._save_embeddings_to_cache()

    logger.info(f"Embeddings initialized: {stats}")
    return stats
```

---

### Phase 4: Semantic Search (2 hours)

#### 4.1 Implement find_similar_examples
**File**: `backend/app/services/knowledge_base_service.py` (REPLACE existing method)

```python
async def find_similar_examples(
    self,
    question: str,
    top_k: int = 3
) -> list[KBExample]:
    """
    Find most semantically similar examples using embeddings.

    Uses cosine similarity between question embedding and example
    embeddings to rank examples by relevance.

    Args:
        question: User's natural language question
        top_k: Number of examples to return (default 3)

    Returns:
        List of top-k most similar examples, ordered by similarity

    Raises:
        ValueError: If embeddings not initialized
    """
    examples = self.get_examples()

    # Ensure embeddings are initialized
    if not examples or examples[0].embedding is None:
        logger.error("Embeddings not initialized, cannot perform similarity search")
        raise ValueError(
            "Embeddings not initialized. Call initialize_embeddings() first."
        )

    # Generate embedding for question
    logger.debug(f"Generating embedding for question: {question}")
    question_embedding = await self.embedding_service.generate_embedding(question)

    # Compute similarity with all examples
    similarities = []
    for example in examples:
        if example.embedding is None:
            logger.warning(f"Example {example.filename} missing embedding, skipping")
            continue

        similarity = self.embedding_service.cosine_similarity(
            question_embedding,
            example.embedding
        )

        similarities.append((similarity, example))

    # Sort by similarity (highest first)
    similarities.sort(reverse=True, key=lambda x: x[0])

    # Log top results
    logger.info(f"Top {top_k} similar examples:")
    for i, (sim, ex) in enumerate(similarities[:top_k]):
        logger.info(f"  {i+1}. {ex.title} (similarity: {sim:.3f})")

    # Return top-k examples
    return [ex for _, ex in similarities[:top_k]]
```

---

### Phase 5: Application Integration (2 hours)

#### 5.1 Update Dependency Injection
**File**: `backend/app/main.py`

```python
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.knowledge_base_service import KnowledgeBaseService

# Initialize services
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
embedding_service = EmbeddingService(openai_client)
kb_service = KnowledgeBaseService(embedding_service)

# Initialize embeddings on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing embeddings on startup...")
    try:
        stats = await kb_service.initialize_embeddings()
        logger.info(f"Embeddings ready: {stats}")
    except Exception as e:
        logger.error(f"Failed to initialize embeddings: {e}")
        # Don't crash app, but warn
```

#### 5.2 Add Admin Endpoint
**File**: `backend/app/api/admin.py`

```python
@router.post("/refresh-embeddings")
async def refresh_embeddings(
    force: bool = False,
    current_user: UserModel = Depends(require_admin)
) -> dict:
    """
    Refresh knowledge base embeddings (admin only).

    Query params:
        force: If true, regenerate all embeddings (ignore cache)

    Returns:
        Statistics about embedding refresh
    """
    logger.info(f"Admin {current_user.username} requested embedding refresh (force={force})")

    try:
        stats = await kb_service.initialize_embeddings(force_regenerate=force)

        return {
            "status": "success",
            "message": "Embeddings refreshed successfully",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to refresh embeddings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh embeddings: {str(e)}"
        )
```

---

### Phase 6: Testing (4 hours)

#### 6.1 Unit Tests
**File**: `tests/services/test_knowledge_base_service.py`

```python
@pytest.mark.asyncio
async def test_find_similar_examples_with_embeddings(kb_service_with_embeddings):
    """Test semantic search returns relevant examples."""

    # Question about drivers
    question = "Show me all available drivers"
    results = await kb_service_with_embeddings.find_similar_examples(question, top_k=3)

    assert len(results) == 3

    # Should return driver-related examples
    titles = [ex.title.lower() for ex in results]
    assert any('driver' in title for title in titles)


@pytest.mark.asyncio
async def test_embeddings_cache_persistence(kb_service, tmp_path):
    """Test embeddings are saved and loaded from cache."""

    # Generate embeddings
    await kb_service.initialize_embeddings()

    # Check cache file exists
    assert kb_service._embeddings_cache_file.exists()

    # Create new service instance
    kb_service_2 = KnowledgeBaseService(embedding_service)

    # Should load from cache
    stats = await kb_service_2.initialize_embeddings()
    assert stats["cached"] > 0
    assert stats["generated"] == 0


@pytest.mark.asyncio
async def test_similarity_ranking_quality(kb_service_with_embeddings):
    """Test that similarity scores are reasonable."""

    question = "drivers with current availability"
    results = await kb_service_with_embeddings.find_similar_examples(question)

    # First result should be highly relevant
    assert "driver" in results[0].title.lower() or "driver" in results[0].sql.lower()

    # Compute similarity for verification
    question_emb = await embedding_service.generate_embedding(question)
    similarity = embedding_service.cosine_similarity(question_emb, results[0].embedding)

    # Should be at least 0.5 similar
    assert similarity > 0.5
```

#### 6.2 Integration Tests
**File**: `tests/integration/test_embedding_workflow.py`

```python
@pytest.mark.asyncio
async def test_end_to_end_query_with_embeddings(client, auth_headers_user):
    """Test full workflow: question → embeddings → SQL generation."""

    # Submit query
    response = client.post(
        "/api/queries",
        json={"natural_language_query": "Show available drivers"},
        headers=auth_headers_user
    )

    assert response.status_code == 200
    data = response.json()

    # Check SQL was generated
    assert data["status"] == "not_executed"
    assert data["generated_sql"] is not None
    assert "driver" in data["generated_sql"].lower()
```

---

### Phase 7: Documentation (1 hour)

#### 7.1 Update CLAUDE.md
Add section:

```markdown
## Knowledge Base with Embeddings

### Architecture
The knowledge base uses OpenAI embeddings for semantic search:

1. **Startup**: Load examples, generate/load embeddings from cache
2. **Query Time**: Generate question embedding, find top-3 similar examples
3. **SQL Generation**: Pass similar examples to LLM as context

### Files
- `data/knowledge_base/*.sql` - SQL examples (40+ files)
- `data/embeddings_cache.pkl` - Pre-computed embeddings (auto-generated)
- `backend/app/services/embedding_service.py` - Embedding utilities

### Admin Operations

**Refresh embeddings** (after adding new examples):
```bash
curl -X POST http://localhost:8000/api/admin/refresh-embeddings \
  -H "Authorization: Bearer $TOKEN"
```

**Force regenerate all embeddings**:
```bash
curl -X POST "http://localhost:8000/api/admin/refresh-embeddings?force=true" \
  -H "Authorization: Bearer $TOKEN"
```

### Cost Tracking
- Model: `text-embedding-3-small`
- Cost: $0.00002 per 1K tokens
- 40 examples × 500 tokens = 20K tokens = **$0.0004 one-time**
- Per query: ~50 tokens = **$0.000001 per query**
```

---

## 🧪 Testing Strategy

### Manual Testing Checklist

```
□ Add new .sql file to data/knowledge_base/
□ Restart server → embeddings auto-generated
□ Submit query related to new example
□ Verify new example appears in top-3 results (check logs)
□ Submit unrelated query
□ Verify new example NOT in top-3 results

Test Questions:
- "Show available drivers" → should return driver examples
- "List delayed activities" → should return delay examples
- "Get customer information" → should return customer examples
```

---

## 📊 Success Metrics

### Before (Current State)
- Returns: All 7 examples (no filtering)
- Relevance: Random (0% precision)
- Cost: $0

### After (With Embeddings)
- Returns: Top 3 most similar examples
- Relevance: 70-90% precision (estimated)
- Cost: ~$0.00001 per query

### Measurement Plan
1. Create test set of 20 questions with known best examples
2. Run both old and new implementations
3. Measure precision@3 (% of relevant examples in top 3)
4. Target: >70% precision improvement

---

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] All tests passing (pytest tests/)
- [ ] Add `numpy` to requirements.txt
- [ ] Set `OPENAI_API_KEY` in production .env
- [ ] Test with production OpenAI account

### Deployment
- [ ] Deploy code changes
- [ ] Embeddings auto-generate on first startup (~30 seconds)
- [ ] Monitor logs for embedding initialization success
- [ ] Test API endpoint: POST /api/queries

### Post-deployment
- [ ] Monitor OpenAI API usage (should be <$0.01/day)
- [ ] Check embedding cache file created: `data/embeddings_cache.pkl`
- [ ] Test admin refresh endpoint
- [ ] Document for team

---

## 💰 Cost Analysis

### One-Time Costs
- Initial 40 examples: 40 × 500 tokens × $0.00002/1K = **$0.0004**
- Cache regeneration (rare): Same as above

### Ongoing Costs (Per 1000 Queries)
- 1000 questions × 50 tokens × $0.00002/1K = **$0.001**
- **Total: $0.001 per 1000 queries** (essentially free)

### Comparison
- Current LLM costs: ~$0.50 per 1000 queries (SQL generation)
- Embeddings add: 0.2% overhead (negligible)

---

## 🔄 Future Enhancements

### Phase 2 (Optional)
1. **Hybrid Search**: Combine embeddings + keyword matching
2. **Query Expansion**: Use LLM to rephrase questions before search
3. **Reranking**: Use small LLM to rerank top candidates
4. **Analytics Dashboard**: Track which examples are most useful

### Scaling Beyond 100 Examples
- Consider vector database (Pinecone, Weaviate, Qdrant)
- Implement approximate nearest neighbor (ANN) search
- Add metadata filtering (e.g., by table, complexity)

---

## 📝 Implementation Timeline

| Phase | Task | Hours | Dependencies |
|-------|------|-------|--------------|
| 1 | Core embedding infrastructure | 4 | OpenAI API key |
| 2 | Cache management | 3 | Phase 1 |
| 3 | Embedding generation | 3 | Phase 1, 2 |
| 4 | Semantic search | 2 | Phase 3 |
| 5 | Application integration | 2 | Phase 4 |
| 6 | Testing | 4 | All phases |
| 7 | Documentation | 1 | All phases |
| **Total** | | **19 hours** | |

**Suggested Schedule**: 3 days (6-7 hours/day)

---

## 🎯 Next Steps

1. **Review this plan** - Approve architecture and approach
2. **Set up OpenAI API** - Ensure `OPENAI_API_KEY` is configured
3. **Add numpy** - `pip install numpy` (for cosine similarity)
4. **Start Phase 1** - Create EmbeddingService
5. **Iterate** - Build, test, refine

---

## 📞 Support & Questions

**Key Files to Reference**:
- Current implementation: `backend/app/services/knowledge_base_service.py:287-319`
- LLM service: `backend/app/services/llm_service.py:151-214`
- Query flow: `backend/app/services/query_service.py:206-278`

**Common Issues**:
- "Embeddings not initialized" → Check startup logs, ensure OpenAI key valid
- "Cache file corrupted" → Delete `data/embeddings_cache.pkl`, restart
- "High API costs" → Check you're using `text-embedding-3-small` (not `ada-002`)

---

**Ready to implement? Start with Phase 1: Core Embedding Infrastructure!**
