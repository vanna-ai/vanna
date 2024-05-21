

def test_regular_imports():
    from vanna.anthropic.anthropic_chat import Anthropic_Chat
    from vanna.base.base import VannaBase
    from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
    from vanna.hf.hf import Hf
    from vanna.local import LocalContext_OpenAI
    from vanna.marqo.marqo import Marqo_VectorStore
    from vanna.mistral.mistral import Mistral
    from vanna.ollama.ollama import Ollama
    from vanna.openai.openai_chat import OpenAI_Chat
    from vanna.openai.openai_embeddings import OpenAI_Embeddings
    from vanna.opensearch.opensearch_vector import OpenSearch_VectorStore
    from vanna.pinecone.pinecone_vector import PineconeDB_VectorStore
    from vanna.remote import VannaDefault
    from vanna.vannadb.vannadb_vector import VannaDB_VectorStore
    from vanna.ZhipuAI.ZhipuAI_Chat import ZhipuAI_Chat
    from vanna.ZhipuAI.ZhipuAI_embeddings import ZhipuAI_Embeddings

def test_shortcut_imports():
    from vanna.anthropic import Anthropic_Chat
    from vanna.base import VannaBase
    from vanna.chromadb import ChromaDB_VectorStore
    from vanna.hf import Hf
    from vanna.marqo import Marqo_VectorStore
    from vanna.mistral import Mistral
    from vanna.ollama import Ollama
    from vanna.openai import OpenAI_Chat, OpenAI_Embeddings
    from vanna.opensearch import OpenSearch_VectorStore
    from vanna.pinecone import PineconeDB_VectorStore
    from vanna.vannadb import VannaDB_VectorStore
    from vanna.vllm import Vllm
    from vanna.ZhipuAI import ZhipuAI_Chat, ZhipuAI_Embeddings
