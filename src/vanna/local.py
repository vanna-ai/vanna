from .chromadb.chromadb_vector import ChromaDB_VectorStore
from .openai.openai_chat import OpenAI_Chat

class LocalContext_OpenAI(ChromaDB_VectorStore, OpenAI_Chat):
    """
    LocalContext_OpenAI class that combines functionalities from ChromaDB_VectorStore and OpenAI_Chat.

    Attributes:
        config (dict, optional): Configuration dictionary for initializing the parent classes.

    Methods:
        __init__(config=None): Initializes the LocalContext_OpenAI instance with the given configuration.
    """
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
