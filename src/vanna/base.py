from abc import ABC, abstractmethod


class VannaBase(ABC):
    def __init__(self, config=None):
        self.config = config

    def generate_sql_from_question(self, question: str, **kwargs) -> str:
        embedding = self.generate_embedding(question, **kwargs)
        self.store_question(question=question, embedding=embedding, **kwargs)
        question_sql_list = self.get_similar_question_sql(embedding, **kwargs)
        ddl_list = self.get_related_ddl(embedding, **kwargs)
        doc_list = self.get_related_documentation(embedding, **kwargs)
        prompt = self.get_prompt(
            question=question,
            question_sql_list=question_sql_list,
            ddl_list=ddl_list,
            doc_list=doc_list,
            **kwargs,
        )
        llm_response = self.submit_prompt(prompt, **kwargs)
        return llm_response

    def get_similar_question_sql(self, embedding: str, **kwargs) -> list:
        question_sql_ids = self.get_similar_question_sql_ids(embedding, **kwargs)
        question_sql_list = self.get_question_sql(question_sql_ids, **kwargs)
        return question_sql_list

    def get_related_ddl(self, embedding: str, **kwargs) -> list:
        ddl_ids = self.get_related_ddl_ids(embedding, **kwargs)
        ddl_list = self.get_ddl(ddl_ids, **kwargs)
        return ddl_list

    def get_related_documentation(self, embedding: str, **kwargs) -> list:
        doc_ids = self.get_related_documentation_ids(embedding, **kwargs)
        doc_list = self.get_documentation(doc_ids, **kwargs)
        return doc_list

    # ----------------- Use Any Embeddings API ----------------- #
    @abstractmethod
    def generate_embedding(self, question: str, **kwargs) -> str:
        pass

    # ----------------- Use Any Database to Store and Retrieve Context ----------------- #
    @abstractmethod
    def store_question(self, question: str, embedding: str, **kwargs) -> None:
        pass

    @abstractmethod
    def store_question_sql(self, question_sql: str, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def store_ddl(self, ddl: str, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def store_documentation(self, doc: str, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def get_question_sql(self, question_sql_ids: list, **kwargs) -> list:
        pass

    @abstractmethod
    def get_documentation(self, doc_ids: list, **kwargs) -> list:
        pass

    @abstractmethod
    def get_ddl(self, ddl_ids: list, **kwargs) -> list:
        pass

    # ----------------- Use Any Vector Database to Store and Lookup Embedding Similarity ----------------- #
    @abstractmethod
    def store_question_sql_embedding(self, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def store_ddl_embedding(self, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def store_documentation_embedding(self, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def get_similar_question_sql_ids(self, embedding: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_related_ddl_ids(self, embedding: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_related_documentation_ids(self, embedding: str, **kwargs) -> list:
        pass

    # ----------------- Use Any Language Model API ----------------- #

    @abstractmethod
    def get_prompt(
        self,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ) -> str:
        pass

    @abstractmethod
    def submit_prompt(self, prompt: str, **kwargs) -> str:
        pass
