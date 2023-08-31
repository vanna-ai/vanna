import json
import uuid
from abc import abstractmethod

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from .base import VannaBase

default_ef = embedding_functions.DefaultEmbeddingFunction()


class ChromaDB_VectorStore(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is not None and "path" in config:
            path = config["path"]
        else:
            path = "."

        self.chroma_client = chromadb.PersistentClient(
            path=path, settings=Settings(anonymized_telemetry=False)
        )
        self.documentation_collection = self.chroma_client.get_or_create_collection(
            name="documentation", embedding_function=default_ef
        )
        self.ddl_collection = self.chroma_client.get_or_create_collection(
            name="ddl", embedding_function=default_ef
        )
        self.sql_collection = self.chroma_client.get_or_create_collection(
            name="sql", embedding_function=default_ef
        )

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        embedding = default_ef([data])
        if len(embedding) == 1:
            return embedding[0]
        return embedding

    def add_question_sql(self, question: str, sql: str, **kwargs):
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
            }
        )
        self.sql_collection.add(
            documents=question_sql_json,
            embeddings=self.generate_embedding(question_sql_json),
            ids=str(uuid.uuid4()),
        )

    def add_ddl(self, ddl: str, **kwargs):
        self.ddl_collection.add(
            documents=ddl,
            embeddings=self.generate_embedding(ddl),
            ids=str(uuid.uuid4()),
        )

    def add_documentation(self, doc: str, **kwargs):
        self.documentation_collection.add(
            documents=doc,
            embeddings=self.generate_embedding(doc),
            ids=str(uuid.uuid4()),
        )

    # Static method to extract the documents from the results of a query
    @staticmethod
    def _extract_documents(query_results) -> list:
        if query_results is None:
            return []

        if "documents" in query_results:
            documents = query_results["documents"]

            if len(documents) == 1 and isinstance(documents[0], list):
                try:
                    documents = [json.loads(doc) for doc in documents[0]]
                except Exception as e:
                    return documents[0]

            return documents

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.sql_collection.query(
                query_texts=[question],
            )
        )

    def get_related_ddl(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.ddl_collection.query(
                query_texts=[question],
            )
        )

    def get_related_documentation(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.documentation_collection.query(
                query_texts=[question],
            )
        )
