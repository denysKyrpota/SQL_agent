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
    - OPENAI_API_KEY or Azure OpenAI credentials must be set in .env file
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

    # Check for either OpenAI or Azure OpenAI configuration
    use_azure = settings.use_azure_openai
    has_separate_embedding = settings.has_separate_embedding_endpoint

    if use_azure:
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            print("❌ ERROR: Azure OpenAI not configured")
            print()
            print("Please set in your .env file:")
            print("  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com")
            print("  AZURE_OPENAI_API_KEY=your-api-key")
            print("  AZURE_OPENAI_DEPLOYMENT=your-chat-deployment")
            print()
            print("For embeddings (can be separate endpoint):")
            print("  AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-embedding-resource.openai.azure.com")
            print("  AZURE_OPENAI_EMBEDDING_API_KEY=your-embedding-api-key")
            print("  AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small")
            print()
            return 1

        print(f"✓ Azure OpenAI configured")
        print(f"  Chat endpoint: {settings.azure_openai_endpoint}")
        print(f"  Chat deployment: {settings.azure_openai_deployment}")

        if has_separate_embedding:
            print(f"✓ Separate embedding endpoint configured")
            print(f"  Embedding endpoint: {settings.azure_openai_embedding_endpoint}")
            print(f"  Embedding deployment: {settings.azure_openai_embedding_deployment}")
        else:
            embedding_model = settings.azure_openai_embedding_deployment or settings.azure_openai_deployment
            print(f"  Embedding deployment: {embedding_model} (same endpoint)")
    else:
        if not settings.openai_api_key:
            print("❌ ERROR: OPENAI_API_KEY not configured")
            print()
            print("Please set OPENAI_API_KEY in your .env file:")
            print("  OPENAI_API_KEY=sk-...")
            print()
            print("Or configure Azure OpenAI:")
            print("  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com")
            print("  AZURE_OPENAI_API_KEY=your-api-key")
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
    has_embeddings = len(examples) - missing_embeddings

    if missing_embeddings == 0:
        print("✓ All examples already have embeddings!")
        print()
        if not force:
            response = input("Regenerate all embeddings with improved format? (y/N): ")
            if response.lower() != 'y':
                print("Skipping embedding generation")
                print()
                print("Tip: Use --force to regenerate with the new question-like format")
                print("     for better semantic matching with user queries.")
                return 0
        print("Will regenerate all embeddings with improved format")
        print()

    # Confirm generation
    print(f"📊 Summary:")
    print(f"   Total examples: {len(examples)}")
    print(f"   Already have embeddings: {has_embeddings}")
    print(f"   Need embeddings: {missing_embeddings}")
    if force:
        print(f"   Mode: Force regenerate ALL ({len(examples)} examples)")
    else:
        print(f"   Mode: Generate missing only ({missing_embeddings} examples)")
    print()

    if not force and missing_embeddings > 0:
        response = input(f"Generate embeddings for {missing_embeddings} examples? (Y/n): ")
        if response.lower() == 'n':
            print("Cancelled")
            return 0
    elif force:
        print("--force specified, regenerating all embeddings")
    print()

    # Generate embeddings
    print("🚀 Generating embeddings...")
    print("   Using batch API for efficiency")
    print("   Using question-like text format for better semantic matching")
    print()

    try:
        stats = await kb_service.generate_embeddings(
            llm_service,
            force_regenerate=force,
            use_batch=True,
        )

        print("=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print()
        print("Embedding generation complete:")
        print(f"  • Total examples: {stats['total_examples']}")
        print(f"  • Embeddings generated: {stats['embeddings_generated']}")
        print(f"  • Embeddings skipped: {stats['embeddings_skipped']}")
        print(f"  • Embeddings failed: {stats.get('embeddings_failed', 0)}")
        print(f"  • Embeddings available: {stats['embeddings_available']}")
        print()
        if stats.get('used_batch_api'):
            print("  ⚡ Used batch API for faster generation")
        if stats.get('tables_found'):
            print(f"  📊 Tables referenced: {', '.join(stats['tables_found'][:10])}")
            if len(stats['tables_found']) > 10:
                print(f"     ... and {len(stats['tables_found']) - 10} more")
        print()
        print("Embeddings saved to: data/knowledge_base/embeddings.json")
        print()
        print("🎉 Your knowledge base is now ready for semantic search!")
        print()
        print("Text format used for embeddings:")
        print("  'Question: [title]'")
        print("  'Description: [description]'")
        print("  'Tables involved: [extracted tables]'")
        print("  'This query helps answer questions about: [title]'")
        print()
        print("This format better matches how users ask questions!")
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
        print("  • API key invalid or expired")
        print("  • Azure deployment name incorrect")
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
