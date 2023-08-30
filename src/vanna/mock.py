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

    def submit_prompt(self, prompt: str, **kwargs) -> str:
        pass
