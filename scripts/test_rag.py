#!/usr/bin/env python3
"""
Test script to verify RAG system with embeddings.

This script tests the semantic search functionality by:
1. Loading knowledge base with embeddings
2. Generating embedding for a test question
3. Finding similar examples
4. Displaying similarity scores
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.llm_service import LLMService
from backend.app.services.knowledge_base_service import KnowledgeBaseService
from backend.app.config import get_settings


async def test_similarity(question: str):
    """Test similarity search for a given question."""
    print("=" * 70)
    print(f"Testing: {question}")
    print("=" * 70)
    print()

    # Initialize services
    llm_service = LLMService()
    kb_service = KnowledgeBaseService()
    settings = get_settings()

    # Load examples
    examples = kb_service.get_examples()
    print(f"✓ Loaded {len(examples)} examples from knowledge base")

    # Check embeddings
    embeddings_count = sum(1 for ex in examples if ex.embedding is not None)
    if embeddings_count == 0:
        print("❌ No embeddings found!")
        print("   Run: python scripts/generate_embeddings.py --force")
        return

    print(f"✓ {embeddings_count}/{len(examples)} examples have embeddings")
    print()

    # Generate question embedding
    print("Generating embedding for question...")
    question_embedding = await llm_service.generate_embedding(question)
    print(f"✓ Generated embedding: {len(question_embedding)} dimensions")
    print()

    # Find similar examples
    print("Finding similar examples...")
    similar_examples, max_similarity = await kb_service.find_similar_examples(
        question=question,
        question_embedding=question_embedding,
        top_k=3
    )
    print()

    # Display results
    print("Results:")
    print("-" * 70)
    for i, example in enumerate(similar_examples, 1):
        # Calculate similarity for this example
        similarity = kb_service._cosine_similarity(
            question_embedding,
            example.embedding
        )
        print(f"{i}. {example.title}")
        print(f"   Filename: {example.filename}")
        print(f"   Similarity: {similarity:.4f} ({similarity * 100:.2f}%)")
        print()

    print("-" * 70)
    print()

    # Check threshold
    threshold = settings.rag_similarity_threshold
    print(f"Similarity threshold: {threshold:.2f}")
    print()

    if max_similarity >= threshold:
        print(f"✅ HIGH SIMILARITY MATCH! (>= {threshold})")
        print(f"   The system will return this example SQL directly:")
        print(f"   → {similar_examples[0].title}")
        print()
        print("   SQL:")
        print("   " + "=" * 66)
        for line in similar_examples[0].sql.split('\n'):
            print(f"   {line}")
        print("   " + "=" * 66)
    else:
        print(f"⚠️  No exact match (< {threshold})")
        print(f"   The system will use these examples as LLM context")
        print(f"   and generate new SQL")
    print()


async def main():
    """Run multiple test cases."""
    print()
    print("🧪 RAG System Test Suite")
    print()

    test_cases = [
        "current driver status",
        "show me driver's status",
        "what is the status of drivers",
        "drivers with expired certificates",
        "activities finished today",
        "completely unrelated question about products",
    ]

    for i, question in enumerate(test_cases, 1):
        if i > 1:
            print("\n" + "=" * 70 + "\n")

        try:
            await test_similarity(question)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print("Test suite complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
