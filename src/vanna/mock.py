import random

from .openai_embeddings import OpenAI_Embeddings


class MockModel(OpenAI_Embeddings):
    def __init__(self, config=None):
        OpenAI_Embeddings.__init__(self, config=config)

    def store_question(self, question: str, embedding: str, **kwargs) -> None:
        pass

    def store_question_sql(self, question_sql: str, embedding: str, **kwargs) -> str:
        pass

    def store_ddl(self, ddl: str, embedding: str, **kwargs) -> str:
        pass

    def store_documentation(self, doc: str, embedding: str, **kwargs) -> str:
        pass

    def get_question_sql(self, question_sql_ids: list, **kwargs) -> list:
        pass

    def get_documentation(self, doc_ids: list, **kwargs) -> list:
        pass

    def get_ddl(self, ddl_ids: list, **kwargs) -> list:
        pass

    def store_question_sql_embedding(self, embedding: str, **kwargs) -> str:
        pass

    def store_ddl_embedding(self, embedding: str, **kwargs) -> str:
        pass

    def store_documentation_embedding(self, embedding: str, **kwargs) -> str:
        pass

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
