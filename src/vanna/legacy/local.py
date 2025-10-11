from .chromadb.chromadb_vector import ChromaDB_VectorStore
from .openai.openai_chat import OpenAI_Chat


class LocalContext_OpenAI(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
