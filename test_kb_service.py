#!/usr/bin/env python3
"""
Quick test script for Knowledge Base Service.

Tests loading SQL examples from data/knowledge_base/
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.services.knowledge_base_service import KnowledgeBaseService


def main():
    print("=" * 60)
    print("Knowledge Base Service Test")
    print("=" * 60)
    print()

    # Initialize service
    service = KnowledgeBaseService()

    # Test 1: Load examples
    print("Test 1: Loading examples...")
    examples = service.get_examples()
    print(f"✓ Loaded {len(examples)} examples")
    print()

    # Test 2: Display example details
    print("Test 2: Example details...")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example.title}")
        print(f"   File: {example.filename}")
        if example.description:
            print(f"   Description: {example.description}")
        print(f"   SQL length: {len(example.sql)} characters")
        print()

    # Test 3: Get example SQL
    print("Test 3: First example SQL preview...")
    if examples:
        first = examples[0]
        print(f"Title: {first.title}")
        print(f"SQL Preview:")
        print(first.sql[:300])
        print("...")
        print()

    # Test 4: Keyword search
    print("Test 4: Keyword search...")
    driver_examples = service.find_examples_by_keyword("driver")
    print(f"✓ Found {len(driver_examples)} examples with 'driver':")
    for ex in driver_examples:
        print(f"  - {ex.title}")
    print()

    # Test 5: Get all examples as text
    print("Test 5: Get all examples as text...")
    sql_list = service.get_all_examples_text()
    print(f"✓ Got {len(sql_list)} SQL queries")
    total_chars = sum(len(sql) for sql in sql_list)
    print(f"✓ Total characters: {total_chars} (~{total_chars // 4} tokens)")
    print()

    # Test 6: Find similar examples (MVP version)
    print("Test 6: Find similar examples...")
    similar = await_sync(service.find_similar_examples("Show me drivers", top_k=3))
    print(f"✓ Got {len(similar)} similar examples")
    print()

    # Test 7: Get stats
    print("Test 7: Knowledge base statistics...")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()

    print("=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


def await_sync(coro):
    """Run async function synchronously for testing."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


if __name__ == "__main__":
    main()
