import random

from .chromadb_vector import ChromaDB_VectorStore
from .openai_embeddings import OpenAI_Embeddings


class MockModel(ChromaDB_VectorStore):
    def __init__(self, config=None):
        # OpenAI_Embeddings.__init__(self, config=config)
        ChromaDB_VectorStore.__init__(self, config=config)

    def get_prompt(
        self,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ) -> str:
        pass

    def get_related_ddl_ids(self, embedding: str, **kwargs) -> list:
        pass

    def get_related_documentation_ids(self, embedding: str, **kwargs) -> list:
        pass

    def get_similar_question_sql_ids(self, embedding: str, **kwargs) -> list:
        pass

    def submit_prompt(self, prompt: str, **kwargs) -> str:
        pass
