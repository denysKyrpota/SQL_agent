#!/usr/bin/env python3
"""
Script to generate embeddings for knowledge base examples.

This script:
1. Loads all SQL examples from data/knowledge_base/
2. Generates embeddings using OpenAI API
3. Saves embeddings to data/knowledge_base/embeddings.json

Usage:
    python scripts/generate_embeddings.py [--force]

Arguments:
    --force    Skip confirmation prompts and regenerate all embeddings

Requirements:
    - OPENAI_API_KEY must be set in .env file
    - Knowledge base examples must exist in data/knowledge_base/
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.llm_service import LLMService
from backend.app.services.knowledge_base_service import KnowledgeBaseService
from backend.app.config import get_settings


async def main(force: bool = False):
    """
    Generate embeddings for all knowledge base examples.

    Args:
        force: If True, skip confirmation prompts and regenerate all embeddings
    """
    print("=" * 70)
    print("Knowledge Base Embedding Generator")
    print("=" * 70)
    print()

    # Check configuration
    settings = get_settings()

    if not settings.openai_api_key:
        print("❌ ERROR: OPENAI_API_KEY not configured")
        print()
        print("Please set OPENAI_API_KEY in your .env file:")
        print("  OPENAI_API_KEY=sk-...")
        print()
        return 1

    print(f"✓ OpenAI API key configured")
    print(f"✓ Embedding model: {settings.openai_embedding_model}")
    print(f"✓ Similarity threshold: {settings.rag_similarity_threshold}")
    print()

    # Initialize services
    print("Initializing services...")
    llm_service = LLMService()
    kb_service = KnowledgeBaseService()
    print("✓ Services initialized")
    print()

    # Load existing examples
    print("Loading knowledge base examples...")
    examples = kb_service.get_examples()
    print(f"✓ Found {len(examples)} examples in knowledge base")
    print()

    if len(examples) == 0:
        print("❌ No examples found in data/knowledge_base/")
        print()
        print("Please add .sql files to data/knowledge_base/ first")
        return 1

    # Display examples
    print("Examples found:")
    for i, example in enumerate(examples, 1):
        status = "✓ Has embedding" if example.embedding else "○ No embedding"
        print(f"  {i}. {example.title} ({example.filename}) - {status}")
    print()

    # Check if any embeddings need to be generated
    missing_embeddings = sum(1 for ex in examples if ex.embedding is None)

    if missing_embeddings == 0:
        print("✓ All examples already have embeddings!")
        print()
        if not force:
            response = input("Regenerate all embeddings? (y/N): ")
            if response.lower() != 'y':
                print("Skipping embedding generation")
                return 0
        else:
            print("--force specified, regenerating all embeddings")

        # Clear existing embeddings
        for example in examples:
            example.embedding = None
        missing_embeddings = len(examples)

    # Confirm generation
    print(f"📊 Summary:")
    print(f"   Total examples: {len(examples)}")
    print(f"   Need embeddings: {missing_embeddings}")
    print()

    if not force:
        response = input(f"Generate embeddings for {missing_embeddings} examples? (Y/n): ")
        if response.lower() == 'n':
            print("Cancelled")
            return 0
    else:
        print("--force specified, proceeding without confirmation")
    print()

    # Generate embeddings
    print("🚀 Generating embeddings...")
    print("   (This will make OpenAI API calls and may take a few seconds)")
    print()

    try:
        stats = await kb_service.generate_embeddings(llm_service)

        print("=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print()
        print("Embedding generation complete:")
        print(f"  • Total examples: {stats['total_examples']}")
        print(f"  • Embeddings generated: {stats['embeddings_generated']}")
        print(f"  • Embeddings skipped: {stats['embeddings_skipped']}")
        print(f"  • Embeddings available: {stats['embeddings_available']}")
        print()
        print("Embeddings saved to: data/knowledge_base/embeddings.json")
        print()
        print("🎉 Your knowledge base is now ready for semantic search!")
        print()
        print("Next steps:")
        print("  1. Start/restart your backend server")
        print("  2. Ask a question that matches one of your examples")
        print("  3. Check logs to see similarity scores")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR!")
        print("=" * 70)
        print()
        print(f"Failed to generate embeddings: {e}")
        print()
        print("Possible issues:")
        print("  • OpenAI API key invalid or expired")
        print("  • Network connection issue")
        print("  • Rate limit exceeded")
        print()
        return 1


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate embeddings for knowledge base examples"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts and regenerate all embeddings'
    )
    args = parser.parse_args()

    try:
        exit_code = asyncio.run(main(force=args.force))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print("Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
