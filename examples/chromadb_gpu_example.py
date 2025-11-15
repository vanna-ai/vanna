"""
Example: Using ChromaDB AgentMemory with GPU acceleration

This example demonstrates how to use ChromaAgentMemory with intelligent
device selection for GPU acceleration when available.
"""

from vanna.integrations.chromadb import (
    ChromaAgentMemory,
    get_device,
    create_sentence_transformer_embedding_function
)


def example_default_usage():
    """Example 1: Use default embedding function (no GPU, no sentence-transformers required)"""
    print("Example 1: Default ChromaDB embedding (CPU-only, no extra dependencies)")

    memory = ChromaAgentMemory(
        persist_directory="./chroma_memory_default"
    )

    print("✓ ChromaAgentMemory created with default embedding function")
    print()


def example_auto_gpu():
    """Example 2: Automatic GPU detection with SentenceTransformers"""
    print("Example 2: Automatic GPU detection")

    # Detect the best available device
    device = get_device()
    print(f"Detected device: {device}")

    # Create embedding function with automatic device selection
    embedding_fn = create_sentence_transformer_embedding_function()

    memory = ChromaAgentMemory(
        persist_directory="./chroma_memory_gpu",
        embedding_function=embedding_fn
    )

    print(f"✓ ChromaAgentMemory created with SentenceTransformer on {device}")
    print()


def example_explicit_cuda():
    """Example 3: Explicitly use CUDA"""
    print("Example 3: Explicitly request CUDA")

    # Explicitly request CUDA
    embedding_fn = create_sentence_transformer_embedding_function(device="cuda")

    memory = ChromaAgentMemory(
        persist_directory="./chroma_memory_cuda",
        embedding_function=embedding_fn
    )

    print("✓ ChromaAgentMemory created with SentenceTransformer on CUDA")
    print()


def example_custom_model_gpu():
    """Example 4: Use a larger model with GPU"""
    print("Example 4: Custom model with GPU acceleration")

    # Use a larger, more accurate model with GPU
    embedding_fn = create_sentence_transformer_embedding_function(
        model_name="sentence-transformers/all-mpnet-base-v2"
    )

    memory = ChromaAgentMemory(
        persist_directory="./chroma_memory_large",
        embedding_function=embedding_fn
    )

    print("✓ ChromaAgentMemory created with all-mpnet-base-v2 model")
    print()


def example_manual_chromadb():
    """Example 5: Manually configure ChromaDB embedding function"""
    print("Example 5: Manual ChromaDB embedding function configuration")

    from chromadb.utils import embedding_functions

    # Manually create and configure the embedding function
    device = get_device()
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        device=device
    )

    memory = ChromaAgentMemory(
        persist_directory="./chroma_memory_manual",
        embedding_function=embedding_fn
    )

    print(f"✓ ChromaAgentMemory created with manual configuration on {device}")
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("ChromaDB AgentMemory GPU Acceleration Examples")
    print("=" * 70)
    print()

    # Example 1: Default (no GPU, no sentence-transformers needed)
    example_default_usage()

    # Examples 2-5 require sentence-transformers to be installed
    try:
        import sentence_transformers

        example_auto_gpu()

        # Only run CUDA example if CUDA is available
        device = get_device()
        if device == "cuda":
            example_explicit_cuda()

        example_custom_model_gpu()
        example_manual_chromadb()

    except ImportError:
        print("⚠️  sentence-transformers not installed")
        print("    Install with: pip install sentence-transformers")
        print("    Examples 2-5 require this package for GPU acceleration")
        print()

    print("=" * 70)
    print("Summary:")
    print("- Example 1 works without sentence-transformers (CPU only)")
    print("- Examples 2-5 require sentence-transformers for GPU support")
    print("- GPU acceleration automatically detected when available")
    print("=" * 70)
