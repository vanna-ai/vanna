def test_regular_imports():
    from vanna.anthropic.anthropic_chat import Anthropic_Chat
    from vanna.azuresearch.azuresearch_vector import AzureAISearch_VectorStore
    from vanna.base.base import VannaBase
    from vanna.bedrock.bedrock_converse import Bedrock_Converse
    from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
    from vanna.cohere.cohere_chat import Cohere_Chat
    from vanna.cohere.cohere_embeddings import Cohere_Embeddings
    from vanna.faiss.faiss import FAISS
    from vanna.google.bigquery_vector import BigQuery_VectorStore
    from vanna.google.gemini_chat import GoogleGeminiChat
    from vanna.hf.hf import Hf
    from vanna.local import LocalContext_OpenAI
    from vanna.marqo.marqo import Marqo_VectorStore
    from vanna.milvus.milvus_vector import Milvus_VectorStore
    from vanna.mistral.mistral import Mistral
    from vanna.ollama.ollama import Ollama
    from vanna.openai.openai_chat import OpenAI_Chat
    from vanna.openai.openai_embeddings import OpenAI_Embeddings
    from vanna.opensearch.opensearch_vector import OpenSearch_VectorStore
    from vanna.opensearch.opensearch_vector_semantic import (
      OpenSearch_Semantic_VectorStore,
    )
    from vanna.pgvector.pgvector import PG_VectorStore
    from vanna.pinecone.pinecone_vector import PineconeDB_VectorStore
    from vanna.qdrant.qdrant import Qdrant_VectorStore
    from vanna.qianfan.Qianfan_Chat import Qianfan_Chat
    from vanna.qianfan.Qianfan_embeddings import Qianfan_Embeddings
    from vanna.qianwen.QianwenAI_chat import QianWenAI_Chat
    from vanna.qianwen.QianwenAI_embeddings import QianWenAI_Embeddings
    from vanna.remote import VannaDefault
    from vanna.vannadb.vannadb_vector import VannaDB_VectorStore
    from vanna.weaviate.weaviate_vector import WeaviateDatabase
    from vanna.xinference.xinference import Xinference
    from vanna.ZhipuAI.ZhipuAI_Chat import ZhipuAI_Chat
    from vanna.ZhipuAI.ZhipuAI_embeddings import ZhipuAI_Embeddings

def test_shortcut_imports():
    from vanna.anthropic import Anthropic_Chat
    from vanna.azuresearch import AzureAISearch_VectorStore
    from vanna.base import VannaBase
    from vanna.chromadb import ChromaDB_VectorStore
    from vanna.cohere import Cohere_Chat, Cohere_Embeddings
    from vanna.faiss import FAISS
    from vanna.hf import Hf
    from vanna.marqo import Marqo_VectorStore
    from vanna.milvus import Milvus_VectorStore
    from vanna.mistral import Mistral
    from vanna.ollama import Ollama
    from vanna.openai import OpenAI_Chat, OpenAI_Embeddings
    from vanna.opensearch import (
      OpenSearch_Semantic_VectorStore,
      OpenSearch_VectorStore,
    )
    from vanna.pgvector import PG_VectorStore
    from vanna.pinecone import PineconeDB_VectorStore
    from vanna.qdrant import Qdrant_VectorStore
    from vanna.qianfan import Qianfan_Chat, Qianfan_Embeddings
    from vanna.qianwen import QianWenAI_Chat, QianWenAI_Embeddings
    from vanna.vannadb import VannaDB_VectorStore
    from vanna.vllm import Vllm
    from vanna.weaviate import WeaviateDatabase
    from vanna.xinference import Xinference
    from vanna.ZhipuAI import ZhipuAI_Chat, ZhipuAI_Embeddings
