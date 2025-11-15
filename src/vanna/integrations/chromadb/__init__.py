"""
ChromaDB integration for Vanna Agents.
"""

from .agent_memory import ChromaAgentMemory


def get_device() -> str:
    """Detect the best available device for embeddings.

    This function checks for GPU availability and returns the appropriate device string
    for use with embedding models. It prioritizes hardware acceleration when available.

    Returns:
        str: Device string - 'cuda' if NVIDIA GPU available, 'mps' if Apple Silicon,
             'cpu' otherwise.

    Examples:
        >>> device = get_device()
        >>> print(f"Using device: {device}")
        Using device: cuda

        # Use with ChromaDB SentenceTransformer embeddings
        >>> from chromadb.utils import embedding_functions
        >>> ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        ...     model_name="sentence-transformers/all-MiniLM-L6-v2",
        ...     device=get_device()
        ... )
        >>> memory = ChromaAgentMemory(embedding_function=ef)
    """
    try:
        import torch

        # Check for CUDA (NVIDIA GPUs)
        if torch.cuda.is_available():
            return "cuda"

        # Check for MPS (Apple Silicon GPUs)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"

    except ImportError:
        # PyTorch not installed, fall back to CPU
        pass

    return "cpu"


def create_sentence_transformer_embedding_function(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = None
):
    """Create a SentenceTransformer embedding function with automatic device detection.

    This convenience function creates a ChromaDB-compatible SentenceTransformer embedding
    function with intelligent device selection. If no device is specified, it automatically
    detects and uses the best available hardware (CUDA, MPS, or CPU).

    Note: This requires the 'sentence-transformers' package to be installed.
    Install with: pip install sentence-transformers

    Args:
        model_name: The name of the sentence-transformer model to use.
                   Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        device: Optional device string ('cuda', 'mps', or 'cpu'). If None,
               automatically detects the best available device.

    Returns:
        A ChromaDB SentenceTransformer embedding function configured for the
        specified/detected device.

    Examples:
        # Automatic device detection (uses CUDA/MPS if available)
        >>> from vanna.integrations.chromadb import ChromaAgentMemory, create_sentence_transformer_embedding_function
        >>> ef = create_sentence_transformer_embedding_function()
        >>> memory = ChromaAgentMemory(embedding_function=ef)

        # Explicitly use CUDA
        >>> ef_cuda = create_sentence_transformer_embedding_function(device="cuda")
        >>> memory = ChromaAgentMemory(embedding_function=ef_cuda)

        # Use a different model
        >>> ef_large = create_sentence_transformer_embedding_function(
        ...     model_name="sentence-transformers/all-mpnet-base-v2"
        ... )
        >>> memory = ChromaAgentMemory(embedding_function=ef_large)
    """
    try:
        from chromadb.utils import embedding_functions
    except ImportError:
        raise ImportError("ChromaDB is required. Install with: pip install chromadb")

    if device is None:
        device = get_device()

    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name, device=device
    )


__all__ = [
    "ChromaAgentMemory",
    "get_device",
    "create_sentence_transformer_embedding_function",
]
